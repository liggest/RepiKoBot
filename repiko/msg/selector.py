
from repiko.core.bot import Bot
from repiko.core.constant import PostType,EventNames
from repiko.msg.message import Message
from repiko.msg.request import RequestData

from fastapi import BackgroundTasks


class BaseSelector:

    ptype=PostType.Unknown
    dataClass=None

    @classmethod
    def isAccept(cls,pt):
        return cls.ptype==pt

    @classmethod
    def getEventName(cls):
        return EventNames.Receive(cls.ptype)

    @classmethod
    def json2Obj(cls,j):
        if cls.dataClass:
            return cls.dataClass.fromJSON(j)
        return None


    def __init__(self,bot:Bot):
        self.bot=bot
        self.eventName=self.getEventName()
        self.backTasks=[]

    def action(self,j,backTasks:BackgroundTasks):
        self.bot.currentSelector=self

        msg=self.json2Obj(j)
        
        self.bot.EM.send(self.eventName,msg,bot=self.bot)

        self.transBackTasks(backTasks)
        return msg

    async def asyncAction(self,j,backTasks:BackgroundTasks):
        self.bot.currentSelector=self
        msg=self.json2Obj(j)
        await self.bot.EM.asyncSend(self.eventName,msg,bot=self.bot)
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

    # def action(self,j,backTasks:BackgroundTasks):
    #     msg:Message=super().action(j,backTasks)
    #     #管理
    #     if msg.realSrc in self.bot.AdminQQ:
    #         if msg.content.startswith("-"):
    #             adminr=self.bot.ac.GetAdminResponse(msg.content)
    #             backTasks.add_task(self.bot.SendStrList,msg.copy(srcAsDst=True),adminr)
    #             # self.bot.SendStrList(msg.copy(srcAsDst=True),adminr)
    #     #响应消息
    #     if not self.bot.IsMe(msg.realSrc): #如果不是自己发的
    #         # msg.content,atMe=self.bot.ClearAtMe(msg.content)
    #         msg.clearAtMe()
    #         if msg.hasAtMe and not msg.isReply:
    #             responseMsg=self.bot.mc.GetAtResponse(msg)
    #             msg.addQuickResponse(responseMsg) # 快速回复
    #         result=self.bot.mc.GetResponse(msg)
    #         backTasks.add_task(self.bot.SendStrList,msg.copy(srcAsDst=True),result)
    #         # self.bot.SendStrList(msg.copy(srcAsDst=True),result)
    #     return msg

    async def asyncAction(self,j,backTasks:BackgroundTasks):
        msg:Message=await super().asyncAction(j,backTasks)
        if msg.realSrc in self.bot.AdminQQ: #管理
            if msg.content.startswith("-"):
                #TODO
                adminr=self.bot.ac.GetAdminResponse(msg.content)
                backTasks.add_task(self.bot.AsyncSendStrs,msg.copy(srcAsDst=True),adminr)
        if not self.bot.IsMe(msg.realSrc): #如果不是自己发的，响应消息
            msg.clearAtMe()
            if msg.hasAtMe and not msg.isReply:
                responseMsg=await self.bot.mc.AsyncAtResponse(msg)
                msg.addQuickResponse(responseMsg) # 快速回复
            result=await self.bot.mc.AsyncResponse(msg)
            backTasks.add_task(self.bot.AsyncSendStrs,msg.copy(srcAsDst=True),result)
        return msg

class NoticeSelector(BaseSelector):

    ptype=PostType.Notice
    dataClass=None

class RequestSelector(BaseSelector):

    ptype=PostType.Request
    dataClass=RequestData

    def __init__(self,bot:Bot):
        super().__init__(bot)

        self.lastRequest=None

    async def asyncAction(self,j,backTasks:BackgroundTasks):
        req:RequestData=await super().asyncAction(j,backTasks)
        
        if self.bot.AdminQQ:
            msg=Message(str(req),dst=0,mtype="private")
            backTasks.add_task(self.bot.AsyncBroadcast,self.bot.AdminQQ,msg)

        self.lastRequest=req

        return req