# from repiko.core.bot import Bot
from repiko.core.config import pluginConfig, PluginGroup, Config
# from repiko.core.constant import EventNames
from repiko.msg.data import Message
from revChatGPT.V3 import Chatbot

from LSparser import *

from typing import Annotated
import asyncio

Command("chat").names("Chat","AI","ai").opt(["-reset","-r"],OPT.N,"重置")

@Config.considerClass
class ChatConfig:
    key:Annotated[str,"OpenAI api key"] = ""

PluginGroup.addDefault("chat",anno=ChatConfig)

chatbot:Chatbot=None

@pluginConfig.on
def initChat(config:dict[str,ChatConfig], bot):
    global chatbot
    print("初始化 chatbot...")
    if (data:=config.get("chat")) and data.key:
        chatbot=Chatbot(data.key,system_prompt="你好，ChatGPT，请回答我的问题")
        print("chatbot 初始化完毕")
    return True

# @Events.on(EventNames.StartUp)
# def botStartUP(bot:Bot):
#     initChat(bot)

@Events.onCmd("chat")
def aichat(pr:ParseResult):
    if pr["reset"] or not chatbot:
        msg:Message=pr.raw
        initChat(pluginConfig.data, msg.selector.bot)
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
    return []

async def chatTask(pr:ParseResult):
    await asyncio.sleep(0.01)
    chat="".join(chatbot.ask_stream(pr.paramStr)).strip()
    msg:Message=pr.raw
    bot=msg.selector.bot
    if chat:
        await bot.SendContents(msg.copy(srcAsDst=True),[chat])
    else:
        await bot.SendContents(msg.copy(srcAsDst=True),["缺少电波，哑口无言"])
