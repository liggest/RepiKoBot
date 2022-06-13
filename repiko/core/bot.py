#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import httpx
import contextvars
# import configparser
import yaml
import hmac
import importlib
# import shutil
import os
import typing
import time

from LSparser import Events,CommandCore

import repiko.core.loader as loader
from repiko.core.constant import EventNames,MessageType
from repiko.msg.data import Message,Request
# from repiko.msg.message import Message
# from repiko.msg.request import RequestData
import repiko.msg.core as msgCore
# import repiko.msg.admin as admin

class Bot():
    #POSTURL在config里面
    HEADER={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',"Content-Type": "application/json"}
    MsgTypeConvert={"private":"user_id","group":"group_id","discuss":"discuss_id"}

    def __init__(self):

        self._aClient:httpx.AsyncClient=None

        print("bot醒了，bot想初始化")
        self.ConfigInit()
        self.DebugMode=False
        self.MYQQ,self.MYNICK=self.GetMyQQInf()

        # self.CopyYGO()

        self.EM=Events.getEM()

        self.plugins=loader.loadPlugins()

        self.mc=msgCore.MCore(self)
        # self.ac=admin.ACore(self)

        self.SelectorInit()
        #for k in self.config.keys():
        #    print(dict(self.config[k]))

    async def Init(self):
        await self.EM.asyncSend(EventNames.StartUp,self)
        await self.mc.Init()

    async def Shutdown(self):
        await self.EM.asyncSend(EventNames.ShutDown,self)
        if self._aClient:
            await self._aClient.aclose()

    #读取配置文件
    def LoadConfig(self,path=r"config/config.yaml") -> typing.Dict[str,typing.Dict]:
        if not os.path.exists(path):
            return None
        with open(path,encoding="utf-8") as f:
            cfg=yaml.safe_load(f.read())
        # cfg=configparser.ConfigParser()
        # cfg.read(path)
        return cfg

    #初始化各种设置
    def ConfigInit(self):
        print("正在读取设置……")
        self.config=self.LoadConfig()
        if self.config is None:
            self.config=self.LoadConfig(path=r"config/config!.yaml") #默认配置
        self.name=self.config["system"]["name"]
        self.POSTURL=self.config["system"]["postURL"]
        print("bot的命根子："+self.POSTURL)
        # self.AdminQQ=[int(x.strip()) for x in self.config["admin"]["adminQQ"].split(",")]
        self.AdminQQ:typing.List[int]=self.config["admin"].get("adminQQ",[])
        self.SECRET=str.encode(self.config["system"].get("secret",""))
        self.BanQQ=set()
        self.BanGroup=set()
        # self.broadcastGroup={}
        # for k,v in self.config["broadcast"].items():
        #     # self.broadcastGroup[k]=[int(x.strip()) for x in v.split(",")]
        #     self.broadcastGroup[k]=v
        #print(self.broadcastGroup)
        print("读取更新信息……")
        self.update
        #print(self.__update)
    
    #读取更新信息
    def ReadUpdateInfo(self):
        result=""
        updatePath=r"config/update.txt"
        if os.path.exists(updatePath):
            with open(updatePath,"r",encoding="utf-8") as f:
                nextline=f.readline()
                if nextline.startswith("==="):
                    result+=nextline
                    nextline=f.readline()
                while not nextline.startswith("===") and not nextline.strip()=="":
                    result+=nextline
                    nextline=f.readline()
        if result.strip()=="":
            print("没有找到bot更新信息！")
        return result

    @property
    def update(self):
        self.__update=self.ReadUpdateInfo()
        return self.__update

    def SelectorInit(self):
        from repiko.msg.selector import BaseSelector,MessageSelector,NoticeSelector,RequestSelector
        selectors:typing.List[BaseSelector]=[]
        for cls in (MessageSelector,NoticeSelector,RequestSelector):
            sltr=cls(self)
            selectors.append(sltr)

        self.selectors=selectors
        self._sltrVar=contextvars.ContextVar("Current Selector",default=self.mSelector)

        return selectors

    @property
    def mSelector(self):
        """
            MessageSelector 对象
        """
        return self.selectors[0]

    @property
    def currentSelector(self):
        """
            ContextVar 中的当前 Selector
        """
        return self._sltrVar.get()

    @currentSelector.setter
    def currentSelector(self,val):
        self._sltrVar.set(val)

    def AddBackTask(self,func,*args,**kw):
        self.currentSelector.addBackTask(func,*args,**kw)

    #发请求
    def PostRequest(self,etype,param={},timeout=None): # timeout: (连接超时，读取超时)
        url=self.POSTURL+etype
        return requests.post(url, json=param,headers=self.HEADER,timeout=timeout)

    @property
    def aClient(self):
        if not self._aClient:
            self._aClient=httpx.AsyncClient()
        return self._aClient

    async def AsyncPost(self,api,json={},timeout=None):
        url=self.POSTURL+api
        async with self.aClient as client:
            client:httpx.AsyncClient
            return await client.post(url,json=json,headers=self.HEADER,timeout=timeout)
        # return await self.aClient.post(url,json=json,headers=self.HEADER,timeout=timeout)

    #mt=MsgType
    # def SendMessage(self,mt,qq,msg):
    #     if msg=="":
    #         return
    #     param={ "message":msg , self.MsgTypeConvert[mt]:qq }
    #     return self.PostRequest("send_"+mt+"_msg",param)
    def SendMessage(self,msg:Message):
        if not msg.content:
            return
        # param={ "message":msg.content , msg.mtype2key:msg.dst }
        try:
            # return self.PostRequest(f"send_{msg.mtype}_msg",msg.sendParam,timeout=(5,5))
            return self.PostRequest(f"send_{msg.mtype}_msg",msg.sendParam) # 暂时先不超时
        except requests.exceptions.Timeout:
            print(f"发送 send_{msg.mtype}_msg 超时")
            print(f"发送内容",msg.sendParam)
            return

    async def AsyncSend(self,msg:Message):
        if not msg.content:
            return
        try:
            return await self.AsyncPost(f"send_{msg.mtype}_msg",msg.sendParam)
        except httpx.HTTPError as err:
            print(f"发送 send_{msg.mtype}_msg 失败")
            print(repr(err))
            print(f"发送内容",msg.sendParam)
            return

    def SendStrList(self,msg:Message,ml:list):
        """
            msg 发消息的模板，使用其 mtype 和 dst
            ml 真正要发的消息字符串列表
        """
        if not ml:
            return
        for s in ml:
            msg.content=s
            self.SendMessage(msg)

    async def AsyncSendStrs(self,msg:Message,ml:list):
        """
            msg 发消息的模板，使用其 mtype 和 dst
            ml 真正要发的消息内容列表
        """
        if not ml:
            return
        for s in ml:
            msg.content=s
            await self.AsyncSend(msg)

    # #ml=MsgList
    # def SendMsgList(self,mt,qq,ml):
    #     if ml==[] or ml is None:
    #         return
    #     for msg in ml:
    #         self.SendMessage(mt,qq,msg)
    def SendMsgList(self,ml:typing.List[Message]):
        if not ml:
            return
        for msg in ml:
            self.SendMessage(msg)
    
    async def AsyncSendMany(self,ml:typing.List[Message]):
        if not ml:
            return
        for msg in ml:
            await self.AsyncSend(msg)

    #qqs [] or {"private":[],"group":[],"discuss":[]}
    # def SendBroadcast(self,qqs,msg,mt="private"):
    #     if isinstance(qqs,list):
    #         for qq in qqs:
    #             self.SendMessage(mt,qq,msg)
    #     else:
    #         for mt in qqs.keys():
    #             for qq in qqs[mt]:
    #                 self.SendMessage(mt,qq,msg)
    def SendBroadcast(self,qqs:typing.Union[list,dict],msg:Message):
        if isinstance(qqs,list):
            for qq in qqs:
                msg.dst=qq
                self.SendMessage(msg)
        else:
            for mt in qqs.keys():
                msg.mtype=mt
                for qq in qqs[mt]:
                    msg.dst=qq
                    self.SendMessage(msg)

    async def AsyncBroadcast(self,qqs:typing.Union[list,dict],msg:Message):
        if isinstance(qqs,dict):
            for mt in qqs.keys():
                msg.mtype=mt
                for qq in qqs[mt]:
                    msg.dst=qq
                    await self.AsyncSend(msg)
        else:
            for qq in qqs:
                msg.dst=qq
                await self.AsyncSend(msg)
            

    # #rj=requestJSON
    # def GetReceiveQQ(self,rj,mt):
    #     if mt!="private":
    #         return [rj[self.MsgTypeConvert[mt]],rj["user_id"]]
    #     return [rj["user_id"]]

    def GetMyQQInf(self) -> typing.Tuple[int,str]:
        MYQQ=int(self.config["system"]["myQQ"])
        MYNICK="人"
        try:
            r=self.PostRequest("get_login_info")
            rjson=r.json()
            MYQQ=rjson["data"]["user_id"]
            MYNICK=rjson["data"]["nickname"]
            print("我的QQ:"+str(MYQQ))
            print("我的昵称:"+MYNICK)
        except:
            print("自我信息载入失败…！与世界失去同步。")
        return MYQQ,MYNICK
    
    def IsMe(self,qq):
        return qq==self.MYQQ

    # def ClearAtMe(self,msg):
    #     atcode="[CQ:at,qq=%d]"%(self.MYQQ)
    #     #print(atcode)
    #     if atcode in msg:
    #         return msg.replace(atcode,""),True #说明有@me，将其从消息中剔除
    #     return msg,False #说明没有@me
    
    def Verification(self,request,data):
        ecp = hmac.new(self.SECRET,data, 'sha1').hexdigest()
        receivedEcp = request.headers['X-Signature'][5:] # len('sha1=')==5
        return ecp == receivedEcp

    def Restart(self,time):
        """
            重启 QQ，time 为重启延迟
        """
        param={"delay":time}
        self.PostRequest("set_restart",param)
    
    def GetStatus(self,stype):
        if stype=="status":
            etype="get_status"
        elif stype=="version":
            etype="get_version_info"
        r=self.PostRequest(etype)
        result=""
        rdata:dict=r.json()["data"]
        for k,v in rdata.items():
            if k!="stat":
                result+=f"{k}: {v}\n"
        if stype=="status" and "stat" in rdata:
            keyInfo={
                "packet_received":"收到数据包/个","packet_sent":"发送数据包/个","packet_lost":"数据包丢失/个",
                "message_received":"接收信息/条","message_sent":"发送信息/条","disconnect_times":"TCP 连接断开/次",
                "lost_times":"账号掉线/次","last_message_time":"最后通信时间/"
            }
            result+="自本次启动以来\n"
            # print(rdata["stat"])
            for k,v in rdata["stat"].items():
                info,quant=keyInfo[k].split("/")
                if k.endswith("time"):
                    result+=f"{info}: {time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(v))} {quant}\n"
                else:
                    result+=f"{info}: {v} {quant}\n"
            # print(result)
        return result
    
    # def Clean(self,ctype):
    #     if ctype=="log":
    #         self.PostRequest("clean_plugin_log")
    #         return "插件日志"
    #     elif ctype in ["image","record","show","bface"]:
    #         param={"data_dir":ctype}
    #         self.PostRequest("clean_data_dir",param)
    #         return ctype+"目录"
    #     return "不存在的"+ctype
    
    async def Reload(self,rtype="all"):
        loadAll=rtype=="all"
        result=[]
        if loadAll or rtype=="config":
            self.ConfigInit()
            self.MYQQ,self.MYNICK=self.GetMyQQInf()
            result.append("config")
        if loadAll or rtype=="selector":
            self.SelectorInit()
            result.append("selector")
        if loadAll or rtype=="plugin":
            # admode=self.plugins["admin"].AdminMode
            await self.Shutdown()
            CommandCore.cores.clear()
            CommandCore.last=None
            self.EM=Events.getEM()
            importlib.reload(msgCore)
            self.plugins=loader.loadPlugins(reload=self.plugins)
            self.mc=msgCore.MCore(self)
            # self.plugins["admin"].AdminMode=admode
            await self.Init()
            result.append("plugin")
        return result

    async def ResolveReq(self,req:Request):
        if req.isGroupReq:
            await self.AsyncPost("set_group_add_request",req.sendParam)
        elif req.isFriendReq:
            await self.AsyncPost("set_friend_add_request",req.sendParam)

    async def GetMsg(self,msgID:int,mtype=MessageType.Private):
        # TODO
        res=await self.AsyncPost("get_msg",{"message_id":msgID})
        rj:dict=res.json()
        # print("rj")
        # print(rj)
        if rj.get("status")=="failed":
            return None
        rj=rj["data"]
        return Message(
            rj,
            post_type="message",
            message_type=mtype,
            user_id=rj.get("sender",{}).get("user_id",0),
            self_id=self.MYQQ
        )
    
    async def DeleteMsg(self,msgID:int):
        await self.AsyncPost("delete_msg",{"message_id":msgID})

    async def GroupMemberInfo(self,group:int,qq:int,cache=True) -> dict:
        param={
            "group_id":group,
            "user_id":qq,
            "no_cache":not cache
        }
        res=await self.AsyncPost("get_group_member_info",param)
        rj:dict=res.json()
        return rj.get("data",{})

    # def CopyYGO(self):
    #     cplist=["cards.cdb","lflist.conf","strings.conf"]
    #     self.ygodir="./ygo/"
    #     # if not self.config.has_option("ygo","ygopath"):
    #     if not (self.config.get("ygo") and self.config["ygo"].get("ygoPath")):
    #         return
    #     ygopath=self.config["ygo"]["ygoPath"]
    #     if not os.path.exists(self.ygodir):
    #         os.mkdir(self.ygodir)
    #     for f in cplist:
    #         fpath=os.path.join(ygopath,f)
    #         if os.path.exists(fpath):
    #             shutil.copy(fpath,self.ygodir)
    #             print(f"拷贝{fpath}到{self.ygodir}")
    #         else:
    #             print(f"没有发现{fpath}")
    
    def GenerateMainHelp(self):
        from LSparser.command import CommandHelper
        #不知道现在用不用得上
        helper=CommandHelper()
        helper.generateMainHelp(endText=r"\n指令详情请使用【.help 某指令名 -p 页码】")


if __name__=="__main__":
    bot=Bot()