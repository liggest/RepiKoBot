from enum import Enum

from repiko.core.bot import Bot
from repiko.msg.message import Message

from fastapi import BackgroundTasks

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
        self.backTasks=[]

    def action(self,j,backTasks:BackgroundTasks):
        msg=self.getJSONData(j)
        
        self.bot.EM.send(self.eventName,msg,bot=self.bot,selector=self)

        self.transBackTasks(backTasks)
        return msg

    def addBackTask(self,func,*args,**kw):
        self.backTasks.append( (func,args,kw) )

    def transBackTasks(self,backTasks:BackgroundTasks):
        while self.backTasks:
            task=self.backTasks.pop(0)
            backTasks.add_task(task[0],*task[1],**task[2])

class MessageSelector(BaseSelector):

    ptype=PostType.Message
    dataClass=Message

    def action(self,j,backTasks:BackgroundTasks):
        msg:Message=super().action(j,backTasks)
        #管理
        if msg.realSrc in self.bot.AdminQQ:
            if msg.content.startswith("-"):
                adminr=self.bot.ac.GetAdminResponse(msg.content)
                backTasks.add_task(self.bot.SendStrList,msg.copy(srcAsDst=True),adminr)
                # self.bot.SendStrList(msg.copy(srcAsDst=True),adminr)
        #响应消息
        if not self.bot.IsMe(msg.realSrc): #如果不是自己发的
            # msg.content,atMe=self.bot.ClearAtMe(msg.content)
            msg.clearAtMe()
            if msg.hasAtMe and not msg.isReply:
                responseMsg=self.bot.mc.GetAtResponse(msg)
                msg.addQuickResponse(responseMsg) # 快速回复
            result=self.bot.mc.GetResponse(msg)
            backTasks.add_task(self.bot.SendStrList,msg.copy(srcAsDst=True),result)
            # self.bot.SendStrList(msg.copy(srcAsDst=True),result)
        return msg


class NoticeSelector(BaseSelector):

    ptype=PostType.Notice
    dataClass=None

class RequestSelector(BaseSelector):

    ptype=PostType.Request
    dataClass=None