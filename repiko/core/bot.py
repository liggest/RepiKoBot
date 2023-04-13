#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# import requests
# import httpx
import contextvars
# import configparser
# import yaml
import importlib
# import shutil
import os
# import typing
import time
from pathlib import Path

from LSparser import Events,CommandCore

import repiko.core.loader as loader
from repiko.core.constant import EventNames,PostType,MessageType,ConnectionMethod
from repiko.core.log import logger
from repiko.core.api import Api
from repiko.core.config import BotConfig, ConnectionInfo
from repiko.config import Config
from repiko.msg.data import BaseData,Message,Request
from repiko.msg.selector import BaseSelector,MessageSelector,NoticeSelector,RequestSelector
# from repiko.msg.message import Message
# from repiko.msg.request import RequestData
import repiko.msg.core as msgCore
# import repiko.msg.admin as admin

class Bot:
    #POSTURL在config里面
    HEADER={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',"Content-Type": "application/json"}
    MsgTypeConvert={"private":"user_id","group":"group_id","discuss":"discuss_id"}

    def __init__(self):

        # self._aClient:httpx.AsyncClient=None

        logger.info("bot 醒了，bot 想初始化")
        self._api:Api=None

        self.EM=Events.getEM()

        self.ConfigInit()
        self.DebugMode=False
        # self.MYQQ,self.MYNICK=self.GetMyQQInf()

        # self.CopyYGO()

        # self.plugins=loader.loadPlugins()

        # self.mc=msgCore.MCore(self)
        # self.ac=admin.ACore(self)

        self.SelectorInit()
        #for k in self.config.keys():
        #    print(dict(self.config[k]))

    async def Init(self):
        self.MYQQ,self.MYNICK=await self.GetMyQQInfo()
        self.plugins=loader.loadPlugins(reload=hasattr(self,"plugins")) # 有 plugins 时重载
        self.mc=msgCore.MCore(self)
        await self.EM.asyncSend(EventNames.Startup,self)
        await self.mc.Init()
        await self.MoreConfigsInit()

        logger.info("bot 说它好了")

    async def Shutdown(self):
        await self.EM.asyncSend(EventNames.Shutdown,self)
        # if self._aClient:
        #     await self._aClient.aclose()

    #读取配置文件
    # def LoadConfig(self,path:Path=None) -> typing.Dict[str,typing.Dict]:
    def LoadConfig(self) -> BotConfig | dict:
        # if not path:
        #     path=Path(r"config/config!.yaml")
        # with path.open(encoding="utf-8") as f:
        #     cfg=yaml.safe_load(f)
        # # cfg=configparser.ConfigParser()
        # # cfg.read(path)
        # return cfg
        from repiko.core.config import config
        if config.data is None:
            return config.init(self)
        return config.data

    # def SaveConfig(self):
    #     from repiko.core.config import config
    #     config.save(self)

    #初始化各种设置
    def ConfigInit(self):
        logger.info("正在读取设置……")
        # path=Path(r"config/config.yaml")
        # self.config=self.LoadConfig(path) if path.exists() else self.LoadConfig() #默认配置
        self.config=self.LoadConfig()
        # logger.debug(repr(self.config))
        # if self.config is None: 
        #     self.config=self.LoadConfig(path) 
        # self.name=self.config["bot"]["name"]
        self.name=self.config.bot.name
        # self.POSTURL=self.config["bot"]["postURL"]
        # self.ConnectionInit(self.config.get("connection",{}))
        self.ConnectionInit(self.config.connection)
        # self.AdminQQ=[int(x.strip()) for x in self.config["admin"]["adminQQ"].split(",")]
        admin=self.config.admin
        self.AdminQQ=[int(qq) for qq in admin.adminQQ if qq]
        # self.SECRET=str.encode(self.config["bot"].get("secret",""))
        self.BanQQ=set()
        self.BanGroup=set()
        # self.broadcastGroup={}
        # for k,v in self.config["broadcast"].items():
        #     # self.broadcastGroup[k]=[int(x.strip()) for x in v.split(",")]
        #     self.broadcastGroup[k]=v
        #print(self.broadcastGroup)
        logger.info("读取更新信息……")
        self.update
        #print(self.__update)

    def ConnectionInit(self,config):
        self.URL:str=None
        self.POSTURL:str=None
        self.SECRET=""
        self.METHOD=ConnectionMethod.Unknown
        ConnectionInfo.get(config,self)
        logger.info(f"bot 的命根子：[{self.METHOD}] {self.URL}")
        
        self._api=Api.fromMethod(self.METHOD,self)
        logger.debug(f"正在使用 {self._api.__class__.__name__}")

    async def MoreConfigsInit(self):
        for config in Config._configs.values():
            await config.asyncInit(self)
        from repiko.core.config import pluginConfig
        if not pluginConfig.saved:
            pluginConfig.save(self)  # 总是在初始化后保存一下 pluginConfig

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
        if not result.strip():
            logger.warning("没有找到bot更新信息！")
        return result

    @property
    def update(self):
        self._update=self.ReadUpdateInfo()
        return self._update

    def SelectorInit(self):
        # selectors:typing.List[BaseSelector]=[]
        # for cls in (MessageSelector,NoticeSelector,RequestSelector):
        #     sltr=cls(self)
        #     selectors.append(sltr)
        self.selectors:list[BaseSelector]=[cls(self) for cls in (MessageSelector,NoticeSelector,RequestSelector)]
        self._sltrVar=contextvars.ContextVar("Current Selector",default=self.mSelector)

        return self.selectors

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

    async def _handleData(self,rj:dict):
        """  处理 event 数据，返回快速操作结果  """
        postType=rj["post_type"]
        #DEBUG
        if self.DebugMode and postType!=PostType.Meta: #不打印心跳
            logger.debug(rj)
        
        sltr=None
        if any(sltr:=s for s in self.selectors if s.isAccept(rj)):
            msg:BaseData=await sltr.asyncAction(rj)
            sltr.runBackTasks()
            if msg and msg.quickReply: # 快速操作
                logger.info(f"quickReply:{msg.replyJson}")
                return msg.replyJson
        return {}

    #发请求
    # def PostRequest(self,api,json={},timeout=None): # timeout: (连接超时，读取超时)
    #     # url=self.POSTURL+etype
    #     url=f"{self.URL}{api}"
    #     return requests.post(url,json=json,headers=self.HEADER,timeout=timeout)
    
    def SyncPost(self, api:str, json:dict=None, timeout=None):
        return self._api.syncPost(api,json,timeout)

    # PostRequest=SyncPost

    # @property
    # def aClient(self):
    #     if not self._aClient:
    #         self._aClient=httpx.AsyncClient()
    #     return self._aClient 

    # async def AsyncPost(self,api,json={},timeout=None):
    #     # url=self.POSTURL+api
    #     url=f"{self.URL}{api}"
    #     # async with self.aClient as client:
    #     async with httpx.AsyncClient() as client:
    #         return await client.post(url,json=json,headers=self.HEADER,timeout=timeout)
    #     # return await self.aClient.post(url,json=json,headers=self.HEADER,timeout=timeout)

    async def Post(self, api:str, json:dict=None, timeout=None):
        return await self._api.post(api,json,timeout)

    # AsyncPost=Post

    #mt=MsgType
    # def SendMessage(self,mt,qq,msg):
    #     if msg=="":
    #         return
    #     param={ "message":msg , self.MsgTypeConvert[mt]:qq }
    #     return self.PostRequest("send_"+mt+"_msg",param)
    # def SendMessage(self,msg:Message):
    #     if not msg.content:
    #         return
    #     # param={ "message":msg.content , msg.mtype2key:msg.dst }
    #     try:
    #         # return self.PostRequest(f"send_{msg.mtype}_msg",msg.sendParam,timeout=(5,5))
    #         return self.PostRequest(f"send_{msg.mtype}_msg",msg.sendParam) # 暂时先不超时
    #     except requests.exceptions.Timeout:
    #         logger.error(f"发送 send_{msg.mtype}_msg 超时")
    #         print(f"发送内容",msg.sendParam)
    #         return

    # async def AsyncSend(self,msg:Message):
    #     if not msg.content:
    #         return
    #     try:
    #         return await self.AsyncPost(f"send_{msg.mtype}_msg",msg.sendParam)
    #     except httpx.HTTPError as err:
    #         logger.error(f"发送 send_{msg.mtype}_msg 失败")
    #         print(repr(err))
    #         print(f"发送内容",msg.sendParam)
    #         return

    async def Send(self,msg:Message):
        return await self._api.send(msg)

    # AsyncSend=Send

    # def SendStrList(self,msg:Message,ml:list):
    #     """
    #         msg 发消息的模板，使用其 mtype 和 dst\n
    #         ml 真正要发的消息字符串列表
    #     """
    #     if not ml:
    #         return
    #     for s in ml:
    #         msg.content=s
    #         self.SendMessage(msg)

    # async def AsyncSendStrs(self,msg:Message,ml:list):
    #     """
    #         msg 发消息的模板，使用其 mtype 和 dst\n
    #         ml 真正要发的消息内容列表
    #     """
    #     if not ml:
    #         return
    #     for s in ml:
    #         msg.content=s
    #         await self.AsyncSend(msg)

    async def SendContents(self, msg:Message, ml:list):
        return await self._api.sendContents(msg, ml)

    # AsyncSendStrs=SendContents

    # #ml=MsgList
    # def SendMsgList(self,mt,qq,ml):
    #     if ml==[] or ml is None:
    #         return
    #     for msg in ml:
    #         self.SendMessage(mt,qq,msg)
    # def SendMsgList(self,ml:typing.List[Message]):
    #     if not ml:
    #         return
    #     for msg in ml:
    #         self.SendMessage(msg)
    
    # async def AsyncSendMany(self,ml:typing.List[Message]):
    #     if not ml:
    #         return
    #     for msg in ml:
    #         await self.AsyncSend(msg)

    async def SendMany(self, ml:list[Message]):
        return await self._api.sendMany(ml)

    # AsyncSendMany=SendMany

    #qqs [] or {"private":[],"group":[],"discuss":[]}
    # def SendBroadcast(self,qqs,msg,mt="private"):
    #     if isinstance(qqs,list):
    #         for qq in qqs:
    #             self.SendMessage(mt,qq,msg)
    #     else:
    #         for mt in qqs.keys():
    #             for qq in qqs[mt]:
    #                 self.SendMessage(mt,qq,msg)
    # def SendBroadcast(self,qqs:typing.Union[list,dict],msg:Message):
    #     if isinstance(qqs,list):
    #         for qq in qqs:
    #             msg.dst=qq
    #             self.SendMessage(msg)
    #     else:
    #         for mt in qqs.keys():
    #             msg.mtype=mt
    #             for qq in qqs[mt]:
    #                 msg.dst=qq
    #                 self.SendMessage(msg)

    # async def AsyncBroadcast(self,qqs:typing.Union[list,dict],msg:Message):
    #     if isinstance(qqs,dict):
    #         for mt in qqs.keys():
    #             msg.mtype=mt
    #             for qq in qqs[mt]:
    #                 msg.dst=qq
    #                 await self.AsyncSend(msg)
    #     else:
    #         for qq in qqs:
    #             msg.dst=qq
    #             await self.AsyncSend(msg)

    async def Broadcast(self, qqs:list|dict, msg:Message):
        return await self._api.broadcast(qqs,msg)

    # AsyncBroadcast=Broadcast

    # #rj=requestJSON
    # def GetReceiveQQ(self,rj,mt):
    #     if mt!="private":
    #         return [rj[self.MsgTypeConvert[mt]],rj["user_id"]]
    #     return [rj["user_id"]]

    # def GetMyQQInf(self) -> typing.Tuple[int,str]:
    async def GetMyQQInfo(self) -> tuple[int,str]:
        MYQQ=int(self.config["bot"]["myQQ"])
        MYNICK="人"
        try:
            # r=self.PostRequest("get_login_info")
            # r=await self.AsyncPost("get_login_info")
            # rjson=r.json()
            rj=await self._api.loginInfo()
            MYQQ:int=rj["user_id"]
            MYNICK:str=rj["nickname"]
            logger.info(f"我的QQ:{MYQQ}")
            logger.info(f"我的昵称:{MYNICK}")
        except:
            logger.error("自我信息载入失败…！与世界失去同步。")
        return MYQQ,MYNICK
    
    def IsMe(self,qq):
        return qq==self.MYQQ

    # def ClearAtMe(self,msg):
    #     atcode="[CQ:at,qq=%d]"%(self.MYQQ)
    #     #print(atcode)
    #     if atcode in msg:
    #         return msg.replace(atcode,""),True #说明有@me，将其从消息中剔除
    #     return msg,False #说明没有@me

    # def Restart(self,time):
    #     """
    #         重启 QQ，time 为重启延迟
    #     """
    #     param={"delay":time}
    #     self.PostRequest("set_restart",param)
    
    async def GetStatus(self,stype):
        if stype=="status":
            rdata=await self._api.status()
            # etype="get_status"
        elif stype=="version":
            rdata=await self._api.versionInfo()
            # etype="get_version_info"
        # r=self.PostRequest(etype)
        result=""
        # rdata:dict=r.json()["data"]
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
            self.MYQQ,self.MYNICK=await self.GetMyQQInfo()
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
            # self.plugins=loader.loadPlugins(reload=self.plugins)
            # self.mc=msgCore.MCore(self)
            # self.plugins["admin"].AdminMode=admode
            await self.Init()
            result.append("plugin")
        return result

    # async def ResolveReq(self,req:Request):
    #     if req.isGroupReq:
    #         await self.AsyncPost("set_group_add_request",req.sendParam)
    #     elif req.isFriendReq:
    #         await self.AsyncPost("set_friend_add_request",req.sendParam)

    async def ResolveReq(self,req:Request):
        return await self._api.resolveReq(req)

    # async def GetMsg(self,msgID:int,mtype=MessageType.Private):
    #     res=await self.AsyncPost("get_msg",{"message_id":msgID})
    #     rj:dict=res.json()
    #     # print("rj")
    #     # print(rj)
    #     if rj.get("status")=="failed":
    #         return None
    #     rj=rj["data"]
    #     return Message(
    #         rj,
    #         post_type="message",
    #         message_type=mtype,
    #         user_id=rj.get("sender",{}).get("user_id",0),
    #         self_id=self.MYQQ
    #     )

    async def GetMsg(self, msgID:int, mtype=MessageType.Private):
        return await self._api.msg(msgID,mtype)
    
    # async def DeleteMsg(self,msgID:int):
    #     await self.AsyncPost("delete_msg",{"message_id":msgID})

    async def DeleteMsg(self, msgID:int):
        return await self._api.deleteMsg(msgID)

    async def GetForward(self, forwardID:str):
        return await self._api.forward(forwardID)
    
    async def SendForward(self, msg:Message):
        """  msg 需包含 MessageType、dst 和全是 Node 的 Content  """
        return await self._api.sendForward(msg)

    # async def GroupMemberInfo(self,group:int,qq:int,cache=True) -> dict:
    #     param={
    #         "group_id":group,
    #         "user_id":qq,
    #         "no_cache":not cache
    #     }
    #     res=await self.AsyncPost("get_group_member_info",param)
    #     rj:dict=res.json()
    #     return rj.get("data",{})

    async def GroupMemberInfo(self, group:int, qq:int, cache=True):
        return await self._api.groupMemberInfo(group,qq,cache)

    async def QQInfo(self, qq:int, cache=True):
        return await self._api.qqInfo(qq,cache)

    async def GroupFileInfo(self, group:int, path:str|Path) -> None|dict:
        if not isinstance(path,Path):
            path=Path(path)
        root=await self.GroupRootFolder(group)
        files=root["files"]
        folders=root["folders"]
        for current in reversed(path.parents):
            if current==Path(".") or current==Path("/"):
                continue
            hasCurrent=False
            for f in folders:
                if f["folder_name"]==current.name:
                    hasCurrent=True
                    sub=await self.GroupSubFolder(group,f["folder_id"])
                    files=sub["files"]
                    folders=sub["folders"]
                    break
            if not hasCurrent:
                return None
        if not path.name:
            return root # 直接返回 root 外部需要额外判断
        if files:
            for f in files:
                if f["file_name"]==path.name:
                    return f
        if folders:
            for f in folders:
                if f["folder_name"]==path.name:
                    return f
        return None

    # async def GroupRootFolder(self,group:int):
    #     param={ "group_id":group }
    #     rj:dict=(await self.AsyncPost("get_group_root_files",param)).json()
    #     return rj.get("data",{})
    
    async def GroupRootFolder(self,group:int):
        return await self._api.groupRootFolder(group)

    # async def GroupSubFolder(self,group:int,folderID:int):
    #     param={ "group_id":group,"folder_id":folderID }
    #     rj:dict=(await self.AsyncPost("get_group_files_by_folder",param)).json()
    #     return rj.get("data",{})

    async def GroupSubFolder(self,group:int):
        return await self._api.groupSubFolder(group)

    # async def GroupFileLink(self,group:int,file:dict) -> str:
    #     param={
    #         "group_id":group,
    #         "file_id":file["file_id"],
    #         "busid":file["busid"]
    #     }
    #     rj:dict=(await self.AsyncPost("get_group_file_url",param)).json()
    #     return rj.get("data",{"url":""})["url"]

    async def GroupFileLink(self, group:int, file:dict):
        return await self._api.groupFileLink(group,file)

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
