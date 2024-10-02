from __future__ import annotations

from repiko.core.constant import PostType,EventNames
from repiko.msg.data import BaseData,Message,Request
# from repiko.msg.message import Message
# from repiko.msg.request import RequestData

from fastapi import BackgroundTasks
# from collections import deque
import asyncio

import typing
if typing.TYPE_CHECKING:
    from repiko.core.bot import Bot


class BaseSelector:

    ptype=PostType.Unknown
    # dataClass=None

    @classmethod
    def isAccept(cls,rjson:dict):
        return cls.ptype==rjson["post_type"]

    @classmethod
    def getEventName(cls):
        return EventNames.Receive(cls.ptype)

    @classmethod
    def json2Obj(cls,rjson:dict) -> BaseData:
        dataCls=BaseData._subs.get(cls.ptype)
        if dataCls:
            return dataCls(rjson)
        # if cls.dataClass:
        #     return cls.dataClass.fromJSON(j)
        return None


    def __init__(self,bot:Bot):
        self.bot=bot
        self.eventName=self.getEventName()
        # self.backTasks=[]
        # self.backTasks=deque()
        self._backTasks=None

    @property
    def backTasks(self):
        if not self._backTasks:
            self._backTasks=BackgroundTasks()
        return self._backTasks

    @backTasks.deleter
    def backTasks(self):
        self._backTasks=None

    # def action(self,rjson,backTasks:BackgroundTasks):
    def action(self,rjson):
        self.bot.currentSelector=self

        msg=self.json2Obj(rjson)
        msg.selector=self
        
        self.bot.EM.send(self.eventName,msg,bot=self.bot)

        # self.transBackTasks(backTasks)
        return msg

    # async def asyncAction(self,rjson,backTasks:BackgroundTasks):
    async def asyncAction(self,rjson):
        self.bot.currentSelector=self
        msg=self.json2Obj(rjson)
        msg.selector=self
        await self.bot.EM.asyncSend(self.eventName,msg,bot=self.bot)
        # self.transBackTasks(backTasks)
        return msg

    def addBackTask(self,func,*args,**kw):
        # self.backTasks.append( (func,args,kw) )
        self.backTasks.add_task(func,*args,**kw)

    # def transBackTasks(self,backTasks:BackgroundTasks):
    # def transBackTasks(self):
    #     while self.backTasks:
    #         task=self.backTasks.pop(0)
    #         backTasks.add_task(task[0],*task[1],**task[2])

    def runBackTasks(self):
        """  用 create_task 运行 backTasks ，不阻塞  """
        if backTasks:=self._backTasks:
            self._backTasks=None
            asyncio.create_task(backTasks())

class MessageSelector(BaseSelector):

    ptype=PostType.Message
    # dataClass=Message

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

    # async def asyncAction(self,rjson,backTasks:BackgroundTasks):
    async def asyncAction(self,rjson):
        # msg:Message=await super().asyncAction(rjson,backTasks)
        msg:Message=await super().asyncAction(rjson)
        # if msg.realSrc in self.bot.AdminQQ: #管理
        #     if msg.content.startswith("-"):
        #         
        #         adminr=self.bot.ac.GetAdminResponse(msg.content)
        #         backTasks.add_task(self.bot.AsyncSendStrs,msg.copy(srcAsDst=True),adminr)
        isFiltered = any(await self.bot.EM.asyncSend(EventNames.MsgFilter, msg, bot=self.bot))
        # isBanned=str(msg.realSrc) in self.bot.BanQQ or (msg.mtype==MessageType.Group and str(msg.src) in self.bot.BanGroup)
        if not (self.bot.IsMe(msg.realSrc) or isFiltered): #如果不是自己发的，响应消息
            # print(repr(msg))
            await msg.clearAtMe()
            if msg.isReply and msg.hasReplyMe:
                responseMsg=await self.bot.mc.AsyncReplyResponse(msg)
                if responseMsg:
                    msg.addQuickReply(responseMsg,atSender=False,replySender=True) # 快速回复消息
            elif msg.hasAtMe:
                responseMsg=await self.bot.mc.AsyncAtResponse(msg)
                if responseMsg:
                    msg.addQuickReply(responseMsg) # 快速回复 带@
            result=await self.bot.mc.AsyncResponse(msg)
            # backTasks.add_task(self.bot.AsyncSendStrs,msg.copy(srcAsDst=True),result)
            # self.addBackTask(self.bot.AsyncSendStrs,msg.copy(srcAsDst=True),result)
            asyncio.create_task(self.bot.SendContents(msg.copy(srcAsDst=True),result))
        return msg

class NoticeSelector(BaseSelector):

    ptype=PostType.Notice
    # dataClass=None

class RequestSelector(BaseSelector):

    ptype=PostType.Request
    # dataClass=RequestData

    def __init__(self,bot:Bot):
        super().__init__(bot)

        self.lastRequest=None

    # async def asyncAction(self,rjson,backTasks:BackgroundTasks):
    #     req:Request=await super().asyncAction(rjson,backTasks)
    async def asyncAction(self,rjson):
        req:Request=await super().asyncAction(rjson) 
        # if self.bot.AdminQQ:
        #     qqs=[ qq for qq in self.bot.AdminQQ if not self.bot.IsMe(qq) ]
        #     msg=Message.build(str(req),dst=0,mtype=MessageType.Private)
        #     backTasks.add_task(self.bot.AsyncBroadcast,qqs,msg)

        self.lastRequest=req

        return req
