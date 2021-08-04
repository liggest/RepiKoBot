#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typing

from LSparser import *
from repiko.module.ygo.dataloader import cdbReader,confReader
from repiko.msg.message import Message

# import repiko.plugin.basic as addCmd

class MCore():

    ModeText={False:"OFF",True:"ON"}

    def __init__(self,bot):
        from repiko.core.bot import Bot
        self.bot:Bot=bot
        self.data={}
        self.data["canteen_meta"]=["新1","新2","新3","新4","老1","老2","楼上楼","清真餐厅","风味餐厅","小南门","大南门","西北风"]
        self.data["canteen_current"]=self.data["canteen_meta"].copy()
        self.data["luckbar"]=["","一","二","三","亖"]
        if bot:
            ygopath=self.bot.ygodir
            self.data["ygocdb"]=cdbReader(path=ygopath+"cards.cdb")
            conf=confReader()
            conf.loadLFlist(ygopath+"lflist.conf")
            conf.loadSets(ygopath+"strings.conf")
            self.data["ygoconf"]=conf

            self.addCmd=self.bot.plugins["basic"]
        else:
            from repiko.core.loader import loadPlugins
            self.addCmd=loadPlugins()["basic"]

        self.cps:typing.List[CommandParser]=[]
        for coreName in CommandCore.cores:
            cp=CommandParser(coreName)
            cp.data["mc"]=self
            self.cps.append( cp )

    
    #sendqq 即rq private时为 [对话者qq] group时为 [群号,消息发送者qq]
    # def GetResponse(self,content,sendqq):
    def GetResponse(self,msg:Message):
        # cp=CommandParser()
        # setattr(cp,"mc",self)
        # setattr(cp,"sendqq",sendqq)
        result=[]
        for cp in self.cps:
            parseResult:ParseResult=cp.tryParse(msg)
            output=parseResult.output
            if output:
                #把parseResult列表里的各个列表拼起来
                for lst in output:
                    if lst:
                        result+=lst
        # parseResult:ParseResult=cp.tryParse(content)
        return result
        # elif parseResult.isCommand():
        #     if not parseResult.isDefinedCommand(): #处理未定义指令
        #         cmd=parseResult.command
        #         if cmd.startswith("rolld") or cmd.startswith("rd"):
        #             return self.addCmd.rolldice(parseResult,cp)
        # return []

    def GetAtResponse(self,content):
        raw=content
        if not isinstance(content,str):
            content=str(content)
        if "是不是" in content:
            return "围观群众：是啊是啊"
        elif "生气了" in content:
            return "没有哦"
        elif "草" in content or "艹" in content:
            return content
        elif "嘤" in content:
            return "我一拳打死一个嘤嘤怪"
        elif "哥" in content or "弟" in content:
            return "欧尼酱~"
        elif "姐" in content or "妹" in content:
            return "欧内酱~"
        elif content.strip()=="弱人工智能" or content.strip()=="鶸人工智能":
            return "你们阉太监也不会动人脑子！"
        elif "来一句" in content or "说一句" in content or "来句话" in content:
            return self.addCmd.aword(None)
        else:
            return "不要碰我呀QwQ"

if __name__=="__main__":
    mc=MCore(None)
    ipt=input("请输入信息：")
    while ipt!="-exit":
        result=mc.GetResponse(ipt,[759851475,1559619324])
        print(result)
        ipt=input("请输入信息：")
    
