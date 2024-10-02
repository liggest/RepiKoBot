from __future__ import annotations

import typing

from repiko.core.constant import MessageType
from repiko.msg.data import Message,Request
from repiko.msg.part import Node

if typing.TYPE_CHECKING:
    from repiko.core.bot import Bot
    from repiko.core.websocket import WS

import httpx
import requests

import asyncio

class ApiError(Exception):

    def __init__(self, data:dict):
        self._data=data
        super().__init__( *filter(None,(self.retcode,self.msg,self.wording)) )

    @property
    def retcode(self):
        return self._data["retcode"]

    @property
    def msg(self):
        return self._data.get("msg","")

    @property
    def wording(self):
        return self._data.get("wording","")

class Api:

    _subs:dict[str,type[Api]]={}

    @classmethod
    def __init_subclass__(subcls):
        # "XXApi" => { "xx":subcls }
        subcls._subs[subcls.__name__.lower().removesuffix(Api.__name__.lower())]=subcls
        super().__init_subclass__()

    @classmethod
    def fromMethod(cls,method:str, bot:Bot):
        subcls=cls._subs[method]
        return subcls(bot)

    def __init__(self, bot:Bot):
        self.bot=bot
        self._timeout=None

    def setTimeout(self,timeout):
        self._timeout=timeout
        return self

    def withTimeout(self,timeout):
        return self.__class__(self.bot).setTimeout(timeout)

    def _syncPost(self, api:str, data:dict=None, timeout=None) -> dict:
        raise NotImplementedError

    async def _post(self, api:str, data:dict=None, timeout=None) -> dict:
        raise NotImplementedError

    def _fetchData(self, rj:dict) -> dict:
        if rj.get("status")=="failed":
            raise ApiError(rj)
        return rj.get("data",{})

    def syncPost(self, api:str, data:dict=None, timeout=None):
        return self._fetchData(self._syncPost(api,data,timeout or self._timeout))
        
    async def post(self, api:str, data:dict=None, timeout=None):
        return self._fetchData(await self._post(api,data,timeout or self._timeout))

    async def send(self, msg:Message):
        if not msg.content:
            return {}
        return await self.post(f"send_{msg.mtype}_msg",msg.sendParam)

    async def sendContents(self, msg:Message, ml:list):
        """
            msg 发消息的模板，使用其 mtype 和 dst\n
            ml 真正要发的 Content 列表
        """
        # if not ml:
        #     return []
        async def sendMsg(c):
            msg.content=c
            if msg.content.isForward:
                return await self.sendForward(msg)
            else:
                return await self.send(msg)
        
        return [await sendMsg(c) for c in ml] # 保持消息有序（？

    async def sendMany(self, ml:list[Message]):
        # if not ml:
        #     return []
        return [await self.send(msg) for msg in ml]

    async def broadcast(self, qqs:list|dict, msg:Message):
        async def sendMsg(mt,qq):
            msg.mtype=mt
            msg.dst=qq
            return await self.send(msg)
        if isinstance(qqs,dict):
            return [await sendMsg(mt,qq) for mt in qqs.keys() for qq in qqs[mt]]
        else:
            return [await sendMsg(msg.mtype,qq) for qq in qqs]
    
    async def resolveReq(self, req:Request):
        if req.isGroupReq:
            await self.post("set_group_add_request",req.sendParam)
        elif req.isFriendReq:
            await self.post("set_friend_add_request",req.sendParam)

    async def loginInfo(self):
        return await self.post("get_login_info")

    async def versionInfo(self):
        return await self.post("get_version_info")

    async def status(self):
        return await self.post("get_status")

    async def msg(self, msgID:int, mtype=MessageType.Private):
        # TODO
        rj=await self.post("get_msg",{ "message_id":msgID })
        return Message(
            rj,
            post_type="message",
            message_type=mtype,
            user_id=rj.get("sender",{}).get("user_id",0),
            self_id=self.bot.MYQQ
        )

    async def deleteMsg(self, msgID:int):
        return await self.post("delete_msg",{ "message_id":msgID })
    
    async def forward(self, forwardID:str) -> list[Node]:
        rj=await self.post("get_forward_msg",{ "message_id":forwardID })
        return [Node.fromEmpty({ "data":msg }) for msg in rj.get("messages",[])]
    
    async def sendForward(self, msg:Message):
        if msg.mtype == MessageType.Group:
            return await self.sendGroupForward(msg.dst, msg.content)
        elif msg.mtype == MessageType.Private:
            return await self.sendPrivateForward(msg.dst, msg.content)
        return {}

    async def sendGroupForward(self, group:int, nodes:list[Node]):
        return await self.post("send_group_forward_msg",{ "group_id":group, "messages":nodes })

    async def sendPrivateForward(self, qq:int, nodes:list[Node]):
        return await self.post("send_private_forward_msg",{ "user_id":qq, "messages":nodes })

    async def groupMemberInfo(self, group:int, qq:int, cache=True):
        return await self.post("get_group_member_info",{ "group_id":group, "user_id":qq, "no_cache":not cache })

    async def qqInfo(self, qq:int, cache=True):
        return await self.post("get_stranger_info",{ "user_id":qq, "no_cache":not cache })

    async def groupRootFolder(self, group:int):
        return await self.post("get_group_root_files",{ "group_id":group })
    
    async def groupSubFolder(self, group:int, folderID:int):
        return await self.post("get_group_files_by_folder",{ "group_id":group, "folder_id":folderID })

    async def groupFileLink(self, group:int, file:dict) -> str:
        param={ "group_id":group, **file }
        return (await self.post("get_group_file_url",param)).get("url","")
    
    async def pasteEmoji(self, msgID:int, emojiID:int):
        return await self.post("set_msg_emoji_like",{ "message_id": msgID, "emoji_id": emojiID })

    async def robotQQRange(self) -> list[dict[str, str]]:  # [ {"minUin": ..., "maxUin": ...} ]
        return await self.post("get_robot_uin_range")

    async def _quickOperation(self, event:dict, operation:dict):
        return await self.post(".handle_quick_operation",{ "context":event, "operation":operation })
         
class HttpApi(Api):

    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.url=self.bot.POSTURL or self.bot.URL # POSTURL 存在则一定是 http 的，URL 可能是 ws 的

    def _syncPost(self, api:str, data:dict=None, timeout=None) -> dict:
        data=data or {}
        url=f"{self.url}{api}"
        return (requests.post(url,json=data,headers=self.bot.HEADER,timeout=timeout)).json()

    async def _post(self, api:str, data:dict=None, timeout=httpx.USE_CLIENT_DEFAULT) -> dict:
        data=data or {}
        url=f"{self.url}{api}"
        async with httpx.AsyncClient() as client:
            return (await client.post(url,json=data,headers=self.bot.HEADER,timeout=timeout)).json()

    async def post(self, api:str, data:dict=None, timeout=httpx.USE_CLIENT_DEFAULT):
        timeout=(timeout or self._timeout) if timeout!=httpx.USE_CLIENT_DEFAULT else (self._timeout or timeout)
        # timeout 非默认时优先用 timeout，否则优先用 self._timeout
        return await super().post(api,data,timeout)

class WSApi(Api):

    def __init__(self, bot: Bot):
        super().__init__(bot)
        self._ws:WS=None

    def _syncPost(self, api:str, data:dict=None, timeout:float|tuple[float]|None=None) -> dict:
        return asyncio.get_event_loop().run_until_complete(self._post(api,data,timeout)) # 不太能用？

    async def _post(self, api:str, data:dict=None, timeout:float|tuple[float]|None=None) -> dict:
        data=data or {}
        return await self._ws._post({ "action":api, "params":data },timeout)
        
class CombinedApi(WSApi):

    def __init__(self, bot: Bot):
        super().__init__(bot)
        self._http=HttpApi(bot)

    def _syncPost(self, api:str, data:dict=None, timeout:float|tuple[float]|None=None) -> dict:
        try:
            return self._http._syncPost(api,data,timeout) # 同步优先用 http
        except requests.exceptions.Timeout:
            return super()._syncPost(api,data,timeout)
            
    async def _post(self, api:str, data:dict=None, timeout:float|tuple[float]|None=None) -> dict:
        try:
            return await super()._post(api,data,timeout) # 异步优先用 WS
        except TimeoutError:
            return await self._http._post(api,data,timeout)
