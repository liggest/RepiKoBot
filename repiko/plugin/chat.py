# from repiko.core.bot import Bot
from repiko.core.log import logger
from repiko.core.config import pluginConfig, PluginUnits, Pattern
from repiko.core.constant import EventNames
from repiko.msg.data import Message
from revChatGPT.V3 import Chatbot
from EdgeGPT import Chatbot as ChatbotV4, ConversationStyle


from LSparser import *

from typing import Annotated, TypedDict, Literal
from typing_extensions import NotRequired
# from enum import Enum
import asyncio
import re

class ChatConfig(Pattern):
    key:Annotated[str | None,"OpenAI api key"]
    cookiePath:Annotated[str | None,"bing cookie path"]

PluginUnits.addDefault("chat",annotation=ChatConfig)

chatbot:Chatbot=None
chatbotV4:ChatbotV4=None

# SysPrompt=("You are ChatGPT, an AI assistant that can access the internet. " 
#            "Internet search results will be sent from the system in JSON format. "
#            "Respond conversationally and cite your sources via a URL at the end of your message. "
#            "那么，你好，ChatGPT，请回答我的问题")
SysPrompt=("你好，ChatGPT，请回答我的问题。" 
           "你可以用网络上的信息回复，将参考链接放在回复的尾部即可。")

@pluginConfig.on
def initChat(config:dict[str,ChatConfig], bot):
    logger.info("初始化 chatbot 们...")
    if (data := config.get("chat")):
        initChatBot(data)
        initChatBotV4(data)
    # return True

def initChatBot(config:ChatConfig):
    global chatbot
    if config and config.key:
        chatbot = Chatbot(config.key,system_prompt=SysPrompt)
        logger.info("chatbot 初始化完毕")
    else:
        logger.warning("无配置，未初始化 chatbot")

def initChatBotV4(config:ChatConfig):
    global chatbotV4
    if config and config.cookiePath:
        chatbotV4 = ChatbotV4(cookie_path=config.cookiePath)
        logger.info("chatbotV4 初始化完毕")
    else:
        logger.warning("无配置，未初始化 chatbotV4")

# @Events.on(EventNames.StartUp)
# def botStartUP(bot:Bot):
#     initChat(bot)

Command("chat").names("Chat","AI","ai").opt(("-reset","-r"),OPT.N,"重置")

@Events.onCmd("chat")
async def aiChat(pr:ParseResult):
    if pr["reset"] or not chatbot:
        # msg:Message=pr.raw
        # initChat(pluginConfig.data, msg.selector.bot)
        initChatBot(pluginConfig.data.get("chat"))
    if not chatbot:
        return ["缺少组件，哑口无言"]
    # res=chatbot.get_chat_response(pr.paramStr)
    # chat="".join(chatbot.ask_stream(pr.paramStr)).strip()
    # if chat:
    #     return [chat]
    # if res and (chat:=res.get("message")):
    #     return [chat]
    # return ["缺少电波，哑口无言"]
    asyncio.create_task(chatTask(pr))
    # return []

def ask(s:str):
    return chatbot.ask(s).strip()

async def chatTask(pr:ParseResult):
    # await asyncio.sleep(0.01)
    chat = await asyncio.get_running_loop().run_in_executor(None,ask,pr.paramStr)
    # chat="".join(chatbot.ask_stream(pr.paramStr)).strip()
    msg:Message = pr.raw
    bot = msg.selector.bot
    if chat:
        await bot.SendContents(msg.copy(srcAsDst=True),[chat])
    else:
        await bot.SendContents(msg.copy(srcAsDst=True),["缺少电波，哑口无言"])

styles = {
    "创意": ConversationStyle.creative,
    "均衡": ConversationStyle.balanced,
    "准确": ConversationStyle.creative,
    "c": ConversationStyle.creative,
    "b": ConversationStyle.balanced,
    "p": ConversationStyle.precise,
    "creative": ConversationStyle.creative,
    "balanced": ConversationStyle.balanced,
    "precise": ConversationStyle.precise,
}

class BingBaseMessage(TypedDict):
    text: str
    author: Literal["user"] | Literal["bot"]
    offense: str

class BingSuggest(BingBaseMessage):
    messageType: Literal["Suggestion"]

class BingSource(TypedDict):
    providerDisplayName: str
    seeMoreUrl: str
    imageLink: NotRequired[str]

class BingMessage(BingBaseMessage):
    spokenText: NotRequired[str]  # 给用户的提问提示
    sourceAttributions: NotRequired[list[BingSource]]
    suggestedResponses: NotRequired[list[BingSuggest]]  # 给用户的提问建议
    messageType: NotRequired[Literal["InternalSearchQuery"] | Literal["InternalSearchResult"] | Literal["InternalLoaderMessage"] | Literal["RenderCardRequest"]]

class BingThrottling(TypedDict):
    maxNumUserMessagesInConversation: int
    numUserMessagesInConversation: int

class BingResult(TypedDict):
    value: Literal["Success"] | str

class BingItem(TypedDict):
    messages:list[BingMessage]
    throttling: BingThrottling
    result: BingResult

class Bing(TypedDict):
    type: int
    item: BingItem

hintMsg = ""
hints:list[BingSuggest] = []
autoReset = False # 聊天前自动重置
queue = asyncio.Queue(maxsize=1)

(Command("bing").names("Bing","chat4","Chat4")
 .opt(("-reset","-r"),OPT.N,"重置")
 .opt(("-style","-s","-风格"),OPT.M,"聊天风格")
 .opt(("-hint","-h","-提示"),OPT.N,"提示文本")
 .opt(("-debug","-d"),OPT.N)
)
@Events.onCmd("bing")
async def bingChat(pr:ParseResult):
    global autoReset
    if not chatbotV4 or autoReset:
        autoReset = False
        initChatBotV4(pluginConfig.data.get("chat"))
    elif pr["reset"]:
        await chatbotV4.close()
        initChatBotV4(pluginConfig.data.get("chat"))
    if not chatbotV4:
        return ["缺少组件，哑口无言"]
    if pr["hint"]:
        result = ""
        if hintMsg:
            result = f"{hintMsg}\n"
        if hints:
            text = "\n".join(f"  {h['text']}" for h in hints)
            result = f"{result}{text}"
        return [result]

    asyncio.create_task(chatTaskV4(pr))
    # return []

async def chatTaskV4(pr:ParseResult):
    style = pr.getByType("style")
    style = styles.get(style,None)
    await queue.put(pr)
    try:
        chat:Bing = await chatbotV4.ask(pr.paramStr,conversation_style=style)
        logger.debug("拿到 chat")
    finally:
        await queue.get()

    if pr["debug"]:
        with open("out.json","w",encoding="utf-8") as f:
            import json
            json.dump(chat,f,indent=4,ensure_ascii=False)

    text = bingText(chat)
    if not text:
        result = ["Bing 暂无回应"]
        if autoReset and not pr.data.get("retrying"):
            pr.data["retrying"] = True  # 标记为正在重试
            await bingChat(pr)          # 无回应且 autoReset 时立即重试
        elif pr.data.get("retrying"):
            logger.error("Bing 重试后依然无回应")
    else:
        result = [text]

    msg:Message=pr.raw
    bot = msg.selector.bot
    await bot.SendContents(msg.copy(srcAsDst=True),result)

refPattern = re.compile(r"\[\^(\d+)\^\]")  # [^1^]

def bingText(chat:Bing):
    global hintMsg, hints, autoReset
    if not (item := chat.get("item")):
        autoReset = True
        return
    if not (msgs := item.get("messages")):
        autoReset = True
        return
    
    limitText = ""
    if limit := item.get("throttling"):
        limitText = f"{limit['numUserMessagesInConversation']} / {limit['maxNumUserMessagesInConversation']}"
        if limit['numUserMessagesInConversation'] == limit['maxNumUserMessagesInConversation']:
            autoReset = True

    for m in reversed(msgs):
        if m["author"] == "bot" and ("messageType" not in m or "suggestedResponses" in m): # 没有 messageType 的是回复
            break
    logger.debug(m)
    if m["author"] != "bot": # 没有回复
        autoReset = True # 下次提问前重置 ChatBotV4
        return
    if text := m.get("text",""):
        text = refPattern.sub(r"[\1]",text)  # [^1^] => [1]
    texts = [text]
    logger.debug(text)

    hintMsg = m.get("spokenText","")
    hints = m.get("suggestedResponses",[])

    logger.debug(f"offense: {repr(m['offense'])}, hint: {repr(hintMsg)}, limit: {limitText}")

    if sources := m.get("sourceAttributions",[]):
        texts.append( "\n".join( f"[{i+1}] {s['seeMoreUrl']}" for i,s in enumerate(sources) ) )

    if limit:
        texts.append(limitText)
    return "\n".join(texts)

@Events.on(EventNames.Shutdown)
async def closeChatBot(bot):
    if chatbotV4:
        await chatbotV4.close()
        logger.info("关闭 chatbotV4")
