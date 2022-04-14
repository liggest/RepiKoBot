#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typing
import asyncio

from LSparser import *
# import LSparser
from repiko.core.constant import EventNames
from repiko.msg.content import Content
from repiko.msg.part import MessagePart,Face
# from repiko.msg.message import Message
from repiko.msg.data import Message

from repiko.msg.assist import CustomParser

import random

class MCore():

    ModeText={False:"OFF",True:"ON"}

    def __init__(self,bot):
        from repiko.core.bot import Bot
        self.bot:Bot=bot
        self.data={}
        if bot:
            self.basic=self.bot.plugins["basic"]
        else:
            from repiko.core.loader import loadPlugins
            self.basic=loadPlugins()["basic"]
        
        self.cps:typing.List[CommandParser]=[]
        for coreName in CommandCore.cores:
            cp=CommandParser(coreName)
            cp._parserCore=CustomParser
            cp.data["mc"]=self
            self.cps.append( cp )
    
    async def Init(self):
        await self.bot.EM.asyncSend(EventNames.MsgCoreInit,self)
    
    #sendqq 即rq private时为 [对话者qq] group时为 [群号,消息发送者qq]
    # def GetResponse(self,content,sendqq):
    # def GetResponse(self,msg:Message):
    #     # cp=CommandParser()
    #     # setattr(cp,"mc",self)
    #     # setattr(cp,"sendqq",sendqq)
    #     result=[]
    #     for cp in self.cps:
    #         parseResult:ParseResult=cp.tryParse(msg)
    #         output=parseResult.output
    #         if output:
    #             #把parseResult列表里的各个列表拼起来
    #             for lst in output:
    #                 if lst:
    #                     result+=lst
    #     # parseResult:ParseResult=cp.tryParse(content)
    #     return result
    #     # elif parseResult.isCommand():
    #     #     if not parseResult.isDefinedCommand(): #处理未定义指令
    #     #         cmd=parseResult.command
    #     #         if cmd.startswith("rolld") or cmd.startswith("rd"):
    #     #             return self.basic.rolldice(parseResult,cp)
    #     # return []

    async def AsyncResponse(self,msg:Message):
        result=[]
        msg=await self.AsyncPreprocess(msg)
        for cp in self.cps:
            parseResult:ParseResult=await cp.asyncTryParse(msg) # pr.raw=msg
            output=parseResult.output
            if output:  #把parseResult列表里的各个列表拼起来
                result+=[ v async for v in self.contentGen(output)]
        return result

    async def AsyncPreprocess(self,msg:Message):
        if msg.isReply:
            hasCmd=any([CustomParser.isCommand(msg,cp) for cp in self.cps]) #能否匹配指令
            if hasCmd:
                replyMsg:Message=await msg.replyMsg
                if replyMsg:
                    # print(repr(replyMsg))
                    await replyMsg.clearAtMe()
                    replyMsg=await self.AsyncPreprocess(replyMsg)
                    msg.content.append(" ")
                    msg.content+=replyMsg.content
        # print(msg)
        return msg


    # async def AsyncResponseGen(self,msg:Message):
    #     for cp in self.cps:
    #         parseResult:ParseResult=await cp.asyncTryParse(msg) # pr.raw=msg
    #         output=parseResult.output
    #         if output:
    #             for val in filter(None,output):
    #                 if asyncio.iscoroutine(val):
    #                     val=await val
    #                 if isinstance(val,Content):
    #                     yield val
    #                 else:
    #                     yield Content(val)
    
    async def contentGen(self,val):
        if not val:
            return
        if MessagePart.isPart(val): # 单个 MessagePart
            yield Content(val)
        elif isinstance(val,typing.Iterable):
            if isinstance(val,Content): # 单个 Content
                yield val
            # elif MessagePart.isPart(val[0]): # 当做是单个 Content
            #     yield Content(val)
            else:
                for newVal in filter(None,val):  # 可能有多个 Content，迭代每个元素，递归做 contentGen
                    async for v in self.contentGen(newVal): # 异步生成器没法 yield from
                        yield v
        elif asyncio.iscoroutine(val):  # 协程
            async for v in self.contentGen(await val): # 异步生成器没法 yield from
                yield v

    # def GetAtResponse(self,content):
    #     raw=content
    #     if not isinstance(content,str):
    #         content=str(content)
    #     if "是不是" in content:
    #         return "围观群众：是啊是啊"
    #     elif "生气了" in content:
    #         return "没有哦"
    #     elif "草" in content or "艹" in content:
    #         return content
    #     elif "嘤" in content:
    #         return "我一拳打死一个嘤嘤怪"
    #     elif "哥" in content or "弟" in content:
    #         return "欧尼酱~"
    #     elif "姐" in content or "妹" in content:
    #         return "欧内酱~"
    #     elif content.strip()=="弱人工智能" or content.strip()=="鶸人工智能":
    #         return "你们阉太监也不会动人脑子！"
    #     elif "来一句" in content or "说一句" in content or "来句话" in content:
    #         return self.basic.aword(None)
    #     else:
    #         return "不要碰我呀QwQ"

    async def AsyncAtResponse(self,msg:Message):
        responses=await self.bot.EM.asyncSend(EventNames.AtMe,msg,self.bot)
        responses=[ v async for v in self.contentGen(responses)]
        if responses:
            # 暂时从所有回复中随机选一个
            return random.choice(responses)

    async def AsyncReplyResponse(self,msg:Message):
        responses=await self.bot.EM.asyncSend(EventNames.ReplyMe,msg,self.bot)
        responses=[ v async for v in self.contentGen(responses)]
        if responses:
            # 暂时从所有回复中随机选一个
            return random.choice(responses)

if __name__=="__main__":
    async def main():
        core=CommandCore.getLast() # 先创建出默认中枢
        mc=MCore(None)
        await core.EM.asyncSend(EventNames.MsgCoreInit,mc)
        ipt=input("请输入信息：")
        while ipt!="-exit":
            # result=mc.GetResponse(ipt,[759851475,1559619324])
            msg=Message.build(ipt,dst=0)
            msg.realSrc=1559619324
            msg.src=759851475
            result=await mc.AsyncResponse(msg)
            print(result)
            ipt=input("请输入信息：")
    
    asyncio.run(main())
    
