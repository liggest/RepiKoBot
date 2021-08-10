
from repiko.core.bot import Bot
from repiko.msg.message import Message
# from repiko.msg.selector import MessageSelector,NoticeSelector,RequestSelector
from repiko.msg.selector import MessageSelector

from LSparser import Events
import random

# @Events.on(MessageSelector.getEventName())
# def repi(msg:Message,bot:Bot):
#     #复读 2%几率复读1次 2‰几率复读3次
#     if not msg or not bot:
#         return
#     factor=random.randint(1,1000)
#     if factor>=500 and factor<520:
#         bot.AddBackTask(bot.SendMessage,msg.copy(srcAsDst=True))
#         # bot.SendMessage(msg.copy(srcAsDst=True))
#     elif factor==1 or factor==1000:
#         bot.AddBackTask(bot.SendMsgList,[msg.copy(srcAsDst=True)]*3)
#         # bot.SendMsgList([msg.copy(srcAsDst=True)]*3)
    
@Events.on(MessageSelector.getEventName())
async def repi(msg:Message,bot:Bot):
    #复读 2%几率复读1次 2‰几率复读3次
    # print("msg",bot.currentSelector)
    if not msg or not bot:
        return
    factor=random.randint(1,1000)
    if factor>=500 and factor<520:
        bot.AddBackTask(bot.AsyncSend,msg.copy(srcAsDst=True))
    elif factor==1 or factor==1000:
        bot.AddBackTask(bot.AsyncSendMany,[msg.copy(srcAsDst=True)]*3)

# @Events.on(NoticeSelector.getEventName())
# async def notice(msg:Message,bot:Bot):
#     print("notice",bot.currentSelector)

# @Events.on(RequestSelector.getEventName())
# async def request(msg:Message,bot:Bot):
#     print("request",bot.currentSelector)