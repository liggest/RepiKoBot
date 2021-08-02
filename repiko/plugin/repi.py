
from repiko.core.bot import Bot
from repiko.msg.message import Message
from repiko.msg.selector import MessageSelector

from LSparser import Events

import random

@Events.on(MessageSelector.getEventName())
def repi(msg:Message,bot:Bot):
    #复读 2%几率复读1次 2‰几率复读3次
    factor=random.randint(1,1000)
    if factor>=500 and factor<520:
        bot.SendMessage(msg.srcAsDst())
    elif factor==1 or factor==1000:
        bot.SendMsgList([msg.srcAsDst()]*3)
    
