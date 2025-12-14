
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
from repiko.module.chat.linkage import LinkedSession
from repiko.module.img.typ import typ_file2png, default_font_paths, default_root_path, default_template_path
from repiko.module.util import images_gen, under_emoji, first_at

from openai.types.chat import ChatCompletionMessageParam
from openai import OpenAIError
from LSparser import Command, Events, ParseResult, OPT


class ChatConfig(Pattern):
    api_key: Annotated[str, "OpenAI style api key"]
    base_url: Annotated[str, "OpenAI style base URL"]
    model_name: Annotated[str, "Model name"]
    mcp_config: Annotated[Path, "MCP config path"] = "config/mcp.json"
    max_tokens: Annotated[int, "Max tokens"] = 32 * 1024
    expire_time: Annotated[int, "Session expire time in seconds"] = 60 * 60 * 2

PluginUnits.addDefault("chat", annotation=ChatConfig)

_llm = None
_mcp = None
_mcp_task = None
_config: ChatConfig | None = None
_sessions: dict[int, Session] = {}

def init_mcp(config_path: Path):
    global _mcp, _mcp_task
    with open(config_path, "r", encoding="utf-8") as f:
        mcp_config: dict = json.load(f)
    
    _mcp = McpServers(mcp_config.get("mcpServers", {}))
    _mcp_task = asyncio.create_task(_mcp.run())

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
async def botShutDown(bot):
    if _mcp:
        _mcp._end.set()
    if _mcp_task:
        await _mcp_task

def get_session(session_id: int) -> Session | None:
    session: Session | None = _sessions.get(session_id)
    if session and not session.is_expired:
        return session
    return None

def ensure_session(session_id: int, reset: bool = False) -> Session:
    session: Session | None = get_session(session_id)
    if not session or reset:
        session = _sessions[session_id] = Session(
            session_id, _config.model_name, McpSystemPrompt(_mcp), _llm, _mcp, _config.expire_time
        )
    return session

def link_session(main: Session, link_id: int) -> LinkedSession | None:
    if not (session_to_link := get_session(link_id)):
        return None  # no session to link

    if isinstance(main, LinkedSession):
        main.link(session_to_link)
    else:
        main = LinkedSession(main, session_to_link)

    _sessions[int(main.id)] = main
    return main

def unlink_session(main: LinkedSession, link_id: int) -> Session:
    main.unlink(link_id)
    if not main.sessions:
        _sessions[int(main.id)] = main.main_session
        main = main.main_session
    return main

def visible_chat(dialog: Dialogue | None):
    if dialog:
        return [message.as_param() for message in dialog.pair]
    return []


def visible_chat_with_error(dialog: Dialogue | None, error: OpenAIError):
    error_param = {"role": "error", "content": str(error)}
    if dialog:
        messages = [dialog[0].as_param(), error_param]
    else:
        messages = [error_param]
    return messages

def whole_dialog_chat(dialog: Dialogue | None):
    if not dialog:
        return
    for message in dialog:
        if isinstance(message.content, ReasoningMessage):
            yield message.content.model_dump(mode="json", exclude_unset=True)
        else:
            yield message.as_param()
        

def session_visible_chat(session: Session):
    for dialog in session.dialogues_gen():
        if not dialog:
            continue
        for message in dialog.pair:
            yield message.as_param()

TemplateBase = default_template_path()

async def render_chat(messages: list[ChatCompletionMessageParam]):
    messages = json.dumps(messages, ensure_ascii=False)
    template_data = {"content": messages, "content_type": "str"}
    ppi = 144
    return Content(*images_gen(
        await asyncio.to_thread(typ_file2png, TemplateBase / "chat_temp.typ", default_font_paths(), root=default_root_path(), ppi=ppi, data=template_data),
        cache=False
    ))

(Command("chat").names("deepseek", "DeepSeek", "ds", "ai", "AI")
 .opt(("-reset", "-r"), OPT.N, "重置会话")
 .opt(("-link", "-l", "-连接", "-连", "-联结", "-链接"), OPT.M, "连接他人的会话")
 .opt(("-unlink", "-unl", "-断开", "-断", "-断连"), OPT.M, "断开与他人的连接")
)

@Events.onCmd("chat")
async def chat(pr: ParseResult):
    if not _llm:
        return ["未配置 chat，当前不可用…"]

    msg: Message = pr.raw
    session_id = msg.realSrc
    actions = []
    return_before_chat = False
    
    if pr["reset"]:
        _sessions.pop(session_id, None)
        actions.append("对话已重置，让我们重新开始吧")

    session = ensure_session(session_id, pr["reset"])
    
    if (link_content := pr.getByType("link")):
        if not (link_at := first_at(link_content)) or not (link_id := link_at.qq_num):
            actions.append("没看懂要和谁的对话连接…")
            return_before_chat = True
        # elif link_id == session_id:
        #     actions.append("最好不要连接自己的对话哦…")
        elif (linked_session := link_session(session, link_id)) is None:
            actions.append("要连接的人什么都没聊过…")
        else:
            session = linked_session
            actions.append(f"成功连接 {link_at.CQcode} 的对话")

    if (unlink_content := pr.getByType("unlink")):
        if not (unlink_at := first_at(unlink_content)) or not (unlink_id := unlink_at.qq_num):
            actions.append("没看懂要和谁的对话断开连接…")
            return_before_chat = True
        elif not isinstance(session, LinkedSession) or unlink_id not in session.sessions:
            actions.append("还没连接过呢，没法断开啦")
        else:
            session = unlink_session(session, unlink_id)
            actions.append(f"成功断开与 {unlink_at.CQcode} 对话的连接")

    content = pr.paramStr.strip()
    if not content:
        if return_before_chat:
            actions.append("要聊点什么吗？整理下参数，再试一次吧")
        else:
            actions.append("要聊点什么吗？")
    else:
        if return_before_chat:
            actions.append("整理下参数，再试一次吧")

    if actions:
        await msg.selector.bot.SendContents(msg.copy(srcAsDst=True), ["\n".join(actions)])

    if not content or return_before_chat:
        return

    async with under_emoji(msg.selector.bot, msg.id, 351):
        dialogue = Dialogue()
        try:
            response = await session.chat(content, current_dialogue=dialogue, temperature=0.6)

            if _config.max_tokens:
                session.rotate(_config.max_tokens)
        except OpenAIError as e:
            messages = visible_chat_with_error(dialogue, e)
            logger.error(repr(e))
            return await render_chat(messages)

        if response.content and (messages := visible_chat(dialogue)):
            # logger.debug(repr(messages))
            return await render_chat(messages)
        return ["结果它什么也没说…！"]

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

(Command("mcp").names("MCP")
 .opt(("-list", "-l"), OPT.N, "当前可用工具列表")
 .opt(("-system", "-sys"), OPT.N, "当前系统提示词")
)

@Events.onCmd("mcp")
async def mcp_cmd(pr: ParseResult):
    if not _mcp:
        return ["未配置 mcp，当前不可用…"]

    if pr["list"]:
        return ["\n".join(mcp_list_tools())]
    
    if pr["system"]:
        return await render_chat([McpSystemPrompt(_mcp).as_param()])

    return ["\n".join(mcp_list_servers())]


def dialogue_by_idx(session: Session, idx: int) -> Dialogue:
    total = len(session._raw_messages)
    idx = min(idx, total - 1)  # 0..n-1
    idx = max(idx, -total)     # -n..-1
    return session._raw_messages[idx]


(Command("chatlog").names("ailog", "对话记录", "历史记录")
 .opt(("-page", "-p", "-页"), OPT.M, "对话轮数（页数），可正可负")
 .opt(("-last", "-tail", "-尾"), OPT.N, "最后一轮对话")
 .opt(("-first", "-head", "-首", "-头"), OPT.N, "第一轮对话")
 .opt(("-text", "-t", "-文本"), OPT.N, "文本形式的最后一轮对话")
 .opt(("-debug", "-d", "-调试"), OPT.N, "包含详细信息的最后一轮对话")
)

@Events.onCmd("chatlog")
async def chatlog(pr: ParseResult):
    if not _llm:
        return ["未配置 chat，当前不可用…"]

    msg: Message = pr.raw

    if (atQQ := first_at(msg.content)) and (qq := atQQ.qq_num):
        session_id = qq
    else:
        session_id = msg.realSrc

    session = get_session(session_id)

    if not session or not session._raw_messages:
        return ["对话记录是空的…"]

    if pr["first"]:
        pr.args["page"] = 1
    if pr["last"]:
        pr.args["page"] = -1

    page: int | None = pr.getToType("page", None, int)

    if page is None and (pr["text"] or pr["debug"]):
        page = -1  # 默认拿最后一轮的文本

    if page is not None:
        # 单页
        idx = page - 1 if page > 0 else page  # 1..n => 0..n-1
        # last_dialogue = session._raw_messages.last_dialogue
        page_dialogue = dialogue_by_idx(session, idx)
        if pr["text"]:
            if page_dialogue:
                return [str(page_dialogue[-1].as_param()["content"]).strip()]
        elif pr["debug"]:
            return await render_chat([*whole_dialog_chat(page_dialogue)])
        elif messages := visible_chat(page_dialogue):
            return await render_chat(messages)
        return ["里面什么也没有…！"]
    
    if messages := [*session_visible_chat(session)]:
        return await render_chat(messages)
    return ["对话记录是空的…"]
            
# (Command("chatbuild").names("tchat")
# )
