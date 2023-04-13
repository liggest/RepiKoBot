from __future__ import annotations

from websockets.client import connect,WebSocketClientProtocol as Client
from websockets.exceptions import ConnectionClosed
import asyncio
import signal

from enum import Enum
import json
import sys

from typing import Callable,Coroutine

from repiko.core.bot import Bot
from repiko.core.log import logger
from repiko.core.constant import PostType,MetaEventType
# from repiko.core.constant import PostType
# from repiko.msg.data import BaseData
# from loguru._defaults

class WS:
    """  正向 WebSocket  """

    class Events(str,Enum):
        Startup="startup"
        Shutdown="shutdown"
        Open="open"
        Close="close"
        Receive="receive"
        Response="response"

    CallbackFunc=Callable[..., None]

    def __init__(self):
        Events=self.Events
        CallbackFunc=self.CallbackFunc
        self._url:str=""
        self._conn:Client=None
        self._hasConn=asyncio.Event()
        self._events:dict[Events,CallbackFunc]={}
        self._firstInit=True
        self._counter=0
        self._echos:dict[int,asyncio.Future]={}
        self._sendTimeout=5.0
        self._postTimeout=30.0
        self._toExit=asyncio.Event()

    async def _getConn(self):
        if self._conn is None:
            await self._hasConn.wait()
        return self._conn

    @property
    def conn(self) -> Coroutine[None,None,Client]:
        return self._getConn()

    @conn.setter
    def conn(self,c:Client):
        if c:
            self._conn=c
            self._hasConn.set()
        else:
            del self.conn

    @conn.deleter
    def conn(self):
        self._conn=None
        self._hasConn.clear()

    @property
    def counter(self):
        self._counter+=1
        self._counter%=sys.maxsize
        return self._counter

    def on(self,name:Events):
        CallbackFunc=self.CallbackFunc
        def inner(func:CallbackFunc):
            self._events[name]=func
            return func
        return inner

    def onStartup(self,func:CallbackFunc):
        return self.on(self.Events.Startup)(func)

    def onShutdown(self,func:CallbackFunc):
        return self.on(self.Events.Shutdown)(func)

    def onReceive(self,func:CallbackFunc):
        return self.on(self.Events.Receive)(func)

    onData=onReceive

    def onResponse(self,func:CallbackFunc):
        return self.on(self.Events.Response)(func)

    async def emit(self,name:Events,*args,**kw):
        func=self._events.get(name)
        if not func:
            return
        if asyncio.iscoroutinefunction(func):
            return await func(*args,**kw)
        return func(*args,**kw)
        
    async def connect(self,url:str):
        self._url=url
        try:
            async with connect(url) as conn:
                self.conn=conn
                logger.info("WebSocket 已连接")
                await self.emit(self.Events.Open,self._conn)
                await self._receive()
        except ConnectionClosed:
            logger.info("WebSocket 连接关闭")
        finally:
            logger.info("WebSocket 已断开")
            await self.emit(self.Events.Close,self._conn)
            del self.conn
            if not self._toExit.is_set():
                return await self.reconnect()

    async def reconnect(self,delay=3.0):
        logger.info(f"WebSocket {delay} 秒后尝试重连")
        await asyncio.sleep(delay)
        return asyncio.create_task(self.connect(self._url))

    async def _receive(self):
        while True:
            data=await self._conn.recv()
            asyncio.create_task(self._handle(data))
    
    _statusFormat={
        "ok":"<green><bold>OK</bold></green>",
        "async":"<yellow><bold>Async</bold></yellow>",
        "failed":"<red><bold>Failed</bold></red>",
    }

    @staticmethod
    def logData(rj:dict):
        ptype=rj["post_type"]
        dtype=rj[f"{ptype}_type"]
        stype=rj.get('sub_type','')
        if ptype==PostType.Meta and dtype==MetaEventType.HeartBeat:
            return
        logger.info(f"WebSocket  新数据  {ptype}  {dtype}  {stype}")

    async def _handle(self,data:str):
        rj:dict=json.loads(data)
        if "echo" in rj:
            logger.opt(colors=True).info(f"WebSocket  新响应  {self._statusFormat[rj['status']]}  {rj['retcode']}")
            if future:=self._echos.get(rj["echo"]):
                future.set_result(rj)
            return
        
        self.logData(rj)
        res=await self.emit(self.Events.Receive,rj)
        if res:
            await self.emit(self.Events.Response,rj,res)

    async def send(self,data:dict|str):
        if not isinstance(data,str):
            data=json.dumps(data,ensure_ascii=False)
        await self._conn.send(data)

    async def _post(self,json:dict=None,timeout:float|tuple[float,float]|None=None) -> dict:
        """  模拟 post  """
        if not json: # 不发空数据
            logger.error("尝试让 Websocket 发送空数据，已提前返回")
            return {}
        if isinstance(timeout,(tuple,list)):
            sendTimeout,postTimeout=timeout
        else:
            sendTimeout,postTimeout=timeout,None
        sendTimeout=sendTimeout or self._sendTimeout
        postTimeout=postTimeout or self._postTimeout
        echo=str(self.counter)
        json["echo"]=echo
        future=asyncio.get_event_loop().create_future()
        self._echos[echo]=future
        try:
            asyncio.create_task(asyncio.wait_for(self.send(json),timeout=sendTimeout))
            return await asyncio.wait_for(future,timeout=postTimeout)
        finally:
            self._echos.pop(echo)

    async def asyncRun(self,url:str):
        conn=None
        try:
            task=asyncio.create_task(self.connect(url))
            conn=await self.conn
            if self._firstInit:
                self._signalCallback()
                logger.info("WebSocket 初始化")
                await self.emit(self.Events.Startup)
                self._firstInit=False
            # await task
            await self._toExit.wait()
        finally:
            if conn:
                await conn.close()
            await task
            logger.info("WebSocket 运行结束")
            await self.emit(self.Events.Shutdown)
            
    def run(self,url:str):
        asyncio.run(self.asyncRun(url))

    # _signals=(signal.SIGTERM,signal.SIGINT)

    def _signalCallback(self):
        sigMap={signal.SIGTERM:"SIGTERM", signal.SIGINT:"SIGINT"}
        def callback(sig:int,frame=None):
            logger.debug(f"检测到 {sigMap[sig]}")
            self._toExit.set()
        try:
            loop=asyncio.get_event_loop()
            for sig in sigMap:
                loop.add_signal_handler(sig,callback,sig)
        except NotImplementedError:
            
            for sig in sigMap:
                signal.signal(sig,callback)


# async def _botHandle(bot:Bot,rj:dict):
#     postType=rj["post_type"]
#     #DEBUG
#     if bot.DebugMode and postType!=PostType.Meta: #不打印心跳
#         logger.debug(rj)
    
#     sltr=None
#     if any(sltr:=s for s in bot.selectors if s.isAccept(rj)):
#         msg:BaseData=await sltr.asyncAction(rj)
#         sltr.runBackTasks()
#         if msg and msg.quickReply: # 快速操作
#             logger.info(f"quickReply:{msg.replyJson}")
#             return msg.replyJson
#     return {}

def main(bot:Bot):
    from repiko.core.api import WSApi
    
    ws=WS()
    
    @ws.onStartup
    async def startup():
        logger.debug("START!")
        if isinstance(bot._api,WSApi):
            bot._api._ws=ws
        await bot.Init()
    
    @ws.onShutdown
    async def shutdown():
        await bot.Shutdown()
        logger.debug("SHUTDOWN!")
        # logger.debug("bot 停机")
    
    ws.onReceive(bot._handleData)
    # @ws.onReceive
    # async def receive(rj:dict):
    #     return await _botHandle(bot,rj)

    @ws.onResponse # 模拟快速操作
    async def response(rj:dict,res:dict):
        # rj.pop("message",None)
        # rj.pop("raw_message",None)
        await bot._api._quickOperation(rj,res)


    ws.run(bot.URL)

if __name__ == "__main__":
    main(Bot())
