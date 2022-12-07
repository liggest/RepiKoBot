from repiko.core.bot import Bot
from repiko.core.constant import EventNames
from repiko.msg.data import Message
from revChatGPT.revChatGPT import Chatbot

from LSparser import *


Command("aichat").names("AIChat","AIchat","AI","ai").opt(["-reset","-r"],OPT.N,"重置")

chatbot:Chatbot=None

def initChat(bot:Bot):
    global chatbot
    print("初始化 chatbot...")
    config=bot.config.get("chat")
    if config:
        chatbot=Chatbot(config, conversation_id=None)
    print("chatbot 初始化完毕")

@Events.on(EventNames.StartUp)
def botStartUP(bot:Bot):
    initChat(bot)

@Events.onCmd("aichat")
def aichat(pr:ParseResult):
    if pr["reset"]:
        msg:Message=pr.raw
        initChat(msg.selector.bot)
    if not chatbot:
        return ["缺少组件，哑口无言"]
    res=chatbot.get_chat_response(pr.paramStr)
    if res and (chat:=res.get("message")):
        return [chat]
    return ["缺少电波，哑口无言"]
