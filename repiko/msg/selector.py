from enum import Enum

from repiko.core.bot import Bot
from repiko.msg.message import Message

class PostType(str,Enum):
    Unknown="unknown" # 一般不用这个
    Message="message"
    Notice="notice"
    Request="request"
    Meta="meta_event"


class BaseSelector:

    ptype=PostType.Unknown
    dataClass=None

    @classmethod
    def isAccept(cls,pt):
        return cls.ptype==pt

    @classmethod
    def getEventName(cls):
        return f"receive-{cls.ptype.name}"

    @classmethod
    def getJSONData(cls,j):
        if cls.dataClass:
            return cls.dataClass.fromJSON(j)
        return None


    def __init__(self,bot:Bot):
        self.bot=bot
        self.eventName=self.getEventName()

    def action(self,j):
        msg=self.getJSONData(j)
        
        self.bot.EM.send(self.eventName,msg,bot=self.bot)
        return msg

class MessageSelector(BaseSelector):

    ptype=PostType.Message
    dataClass=Message

    def action(self, j):
        msg:Message=super().action(j)
        #管理
        if msg.realSrc in self.bot.AdminQQ:
            if msg.content.startswith("-"):
                adminr=self.bot.ac.GetAdminResponse(msg.content)
                self.bot.SendStrList(msg.mtype,msg.src,adminr)
        #响应消息
        if not self.bot.IsMe(msg.realSrc): #如果不是自己发的
            msg.content,atMe=self.bot.ClearAtMe(msg.content)
            if atMe:
                responseMsg=self.bot.mc.GetAtResponse(msg.content)
                msg.addQuickResponse(responseMsg) # 快速回复
            result=self.bot.mc.GetResponse(msg.content,msg.srcList)
            self.bot.SendStrList(msg.mtype,msg.src,result)
        return msg


class NoticeSelector(BaseSelector):

    ptype=PostType.Notice
    dataClass=None

class RequestSelector(BaseSelector):

    ptype=PostType.Request
    dataClass=None