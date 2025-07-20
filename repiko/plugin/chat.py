
from typing import Annotated
from pathlib import Path
import json
import asyncio

from repiko.core.constant import EventNames
from repiko.core.config import pluginConfig, PluginUnits, Pattern
from repiko.core.log import logger
from repiko.msg.data import Message
from repiko.msg.content import Content

from repiko.module.chat.model import LLM, Session, Dialogue, ReasoningMessage
from repiko.module.chat.mcp import McpServers
from repiko.module.chat.prompt import McpSystemPrompt
from repiko.module.img.typ import typ_file2png, default_font_paths, default_root_path
from repiko.module.util import images_gen, under_emoji

from openai.types.chat import ChatCompletionMessageParam
from LSparser import Command, Events, ParseResult, OPT


class ChatConfig(Pattern):
    api_key: Annotated[str, "OpenAI style api key"]
    base_url: Annotated[str, "OpenAI style base URL"]
    model_name: Annotated[str, "Model name"]
    mcp_config: Annotated[Path, "MCP config path"] = "config/mcp.json"
    max_tokens: Annotated[int, "Max tokens"] = 32 * 1024
    expire_time: Annotated[int, "Session expire time in seconds"] = 60 * 60

PluginUnits.addDefault("chat", annotation=ChatConfig)

_llm = None
_mcp = None
_config: ChatConfig | None = None
_sessions = {}

def init_mcp(config_path: Path):
    global _mcp
    with open(config_path, "r", encoding="utf-8") as f:
        mcp_config: dict = json.load(f)
    
    _mcp = McpServers(mcp_config.get("mcpServers", {}))
    asyncio.create_task(_mcp.run())

@pluginConfig.on
def init_chat(config:dict[str, ChatConfig], bot):
    global _llm, _config
    _config = config.get("chat")

    if not _config or (not _config.api_key or not _config.base_url or not _config.model_name):
        logger.warning("无配置，未初始化 chat")
        _config = None
        return
    
    logger.info("初始化 chat...")

    _llm = LLM(api_key=_config.api_key, base_url=_config.base_url)
    init_mcp(_config.mcp_config)

@Events.on(EventNames.Shutdown)
def botShutDown(bot):
    if _mcp:
        _mcp._end.set()

def get_session(session_id: int, reset: bool = False) -> Session:
    session: Session = _sessions.get(session_id)
    if not session or session.is_expired or reset:
        session = _sessions[session_id] = Session(
            session_id, _config.model_name, McpSystemPrompt(_mcp), _llm, _mcp, _config.expire_time
        )
    return session

def visible_chat(dialog: Dialogue):
    if dialog:
        return [message.as_param() for message in dialog.pair]
    return []

def all_dialog_chat(dialog: Dialogue):
    if not dialog:
        return
    for message in dialog:
        if isinstance(message.content, ReasoningMessage):
            yield message.content.model_dump(mode="json", exclude_unset=True)
        else:
            yield message.as_param()
        

def all_visible_chat(session: Session):
    for dialog in session._raw_messages:
        if not dialog:
            continue
        for message in dialog.pair:
            yield message.as_param()


async def render_chat(messages: list[ChatCompletionMessageParam]):
    messages = json.dumps(messages, ensure_ascii=False)
    template_data = {"content": messages, "content_type": "str"}
    ppi = 144
    return Content(*images_gen(
        await asyncio.to_thread(typ_file2png, TemplateBase / "chat_temp.typ", default_font_paths(), root=default_root_path(), ppi=ppi, data=template_data)
    ))

(Command("chat").names("deepseek", "DeepSeek", "ds")
 .opt(("-reset", "-r"), OPT.N, "重置会话")
)

@Events.onCmd("chat")
async def chat(pr: ParseResult):
    if not _llm:
        return ["未配置 chat，当前不可用…"]

    msg: Message = pr.raw
    session_id = msg.realSrc

    session = get_session(session_id, pr["reset"])
    
    async with under_emoji(msg.selector.bot, msg.id, 351):
        response = await session.chat(pr.paramStr, temperature=0.6)
        if _config.max_tokens:
            session.rotate(_config.max_tokens)

        if response.content and (messages := visible_chat(session._raw_messages.last_dialogue)):
            # logger.debug(repr(messages))
            return await render_chat(messages)
        return ["它什么也没说…！"]

(Command("mcp").names("MCP")
 .opt(("-list", "-l"), OPT.N, "列出当前可用的 MCP")
 .opt(("-system", "-sys"), OPT.N, "列出当前系统提示词")
)

def mcp_list_servers():
    for server in _mcp.servers:
        if server.is_inited:
            yield f"✅ {server.name}"
        else:
            yield f"❌ {server.name}"

def mcp_list_tools():
    indent = " " * 2
    for server in _mcp.servers:
        if not server._tools:
            continue
        yield server.name
        for tool in server._tools:
            if tool in _mcp.tool2server or _mcp.wrap_tool_name(tool) in _mcp.tool2server:
                yield f"{indent}{tool}"

TemplateBase = Path("typ/template")

@Events.onCmd("mcp")
async def mcp_cmd(pr: ParseResult):
    if not _mcp:
        return ["未配置 mcp，当前不可用…"]

    if pr["list"]:
        return ["\n".join(mcp_list_tools())]
    
    if pr["system"]:
        return await render_chat([McpSystemPrompt(_mcp).as_param()])

    return ["\n".join(mcp_list_servers())]

(Command("chatlog").names("对话记录", "历史记录")
 .opt(("-last", "-tail", "-尾"), OPT.N, "最后一轮对话")
 .opt(("-text", "-t"), OPT.N, "文本形式的最后一轮对话")
 .opt(("-debug", "-d"), OPT.N, "包含详细信息的最后一轮对话")
)

@Events.onCmd("chatlog")
async def chatlog(pr: ParseResult):
    if not _llm:
        return ["未配置 chat，当前不可用…"]

    msg: Message = pr.raw
    session_id = msg.realSrc

    if session_id not in _sessions:
        return ["对话记录是空的…"]
    
    session = get_session(session_id)

    if pr["text"] or pr["debug"]:
        pr.args["last"] = True  # 只能拿最后一轮的文本

    if pr["last"]:
        if pr["text"]:
            if session._raw_messages.last_dialogue:
                return [str(session._raw_messages.last_dialogue[-1].as_param()["content"]).strip()]
        elif pr["debug"]:
            return await render_chat(list(all_dialog_chat(session._raw_messages.last_dialogue)))
        elif messages := visible_chat(session._raw_messages.last_dialogue):
            return await render_chat(messages)
        return ["它什么也没说…！"]
    
    if messages := [*all_visible_chat(session)]:
        return await render_chat(messages)
    return ["对话记录是空的…"]
            
# (Command("chatbuild").names("tchat")
# )
