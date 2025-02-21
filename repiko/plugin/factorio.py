
from functools import cached_property
from itertools import chain
from typing import Annotated, TYPE_CHECKING
import asyncio
import re
# from datetime import time

from repiko.core.log import logger
from repiko.core.config import pluginConfig, PluginUnits, Pattern
from repiko.msg.data import Message
from repiko.msg.content import Content
from repiko.msg.part import Image
from repiko.module.img.str2image import str2greyPng
from repiko.msg.util import CQunescape

from httpx import AsyncClient
from factorio_rcon import AsyncRCONClient, InvalidResponse, RCONNetworkError

from LSparser import Command, Events, ParseResult, OPT

class PanelConfig(Pattern):
    url: Annotated[str, "panel url"]
    apikey: Annotated[str, "panel apikey"]
    instance_id: Annotated[str, "instance id of factorio in panel"]
    daemon_id: Annotated[str, "daemon id of factorio in panel"]

class FactorioConfig(Pattern):
    host: Annotated[str, "RCON host"] = "127.0.0.1"
    port: Annotated[int, "RCON port"] = 12345
    password: Annotated[str, "RCON password"] = "<password>"
    if TYPE_CHECKING:
        panel: Annotated[PanelConfig | None, "panel config"]

FactorioConfig.addDefault("panel", annotation=Annotated[PanelConfig, "panel config"])

PluginUnits.addDefault("factorio", annotation=FactorioConfig)

class Client:

    task: asyncio.Task | None = None
    client: AsyncRCONClient | None = None
    _end: asyncio.Event | None = None

    def __init__(self, config: FactorioConfig | None):
        self.init(config)

    def init(self, config: FactorioConfig):
        logger.info("初始化 factorio RCON...")
        self.config = config
        if not self.is_configed:
            logger.warning("无配置，未初始化 factorio RCON")
            return

        if self.task is not None:
            self.task.cancel()
            del self.task
        
        self.task = asyncio.create_task(self.run(config.host, config.port, config.password))
        self.task.add_done_callback(self.on_done)

    @property
    def is_configed(self):
        return self.config is not None and self.config.host and self.config.port

    @property
    def is_inited(self):
        return self.client is not None

    async def run(self, host: str, port: int, password: str):
        try:
            self._end = asyncio.Event()
            async with AsyncRCONClient(host, port, password) as self.client:
                logger.info("RCON 已连接")
                # await self.reveive()
                await self.hang()
        finally:
            logger.info("RCON 已断开")
            if self.client is not None:
                del self.client
            if self._end is not None:
                self._end.set()
                del self._end

    async def hang(self):
        await self._end.wait()

    # async def reveive(self):
    #     while True:
    #         try:
    #             response = await self.client.receive_packet()
    #         except (RCONReceiveError, InvalidResponse) as e:
    #             logger.warning(f"RCON 接收消息错误：{e!r}")
    #             continue

    #         if response.body:
    #             logger.info(f"RCON 接收消息: {response.body}")

    def on_done(self, task: asyncio.Task):
        if task.cancelled():
            logger.info("RCON 连接已被取消")
            return
        if task.exception() is not None:
            logger.warning(f"RCON 异常断开，正在重连… \n{task.exception()!r}")
            self.init(self.config)
    
    async def send(self, command: str):
        try:
            return await self._send(command)
        except RCONNetworkError:
            logger.warning("RCON 发送消息失败，在重连后重试一次...")
            self.init(self.config)
            return await self._send(command)
    
    async def _send(self, command: str):
        assert self.client
        logger.info(f"RCON 发送消息: {command}")
        if data := await self.client.send_command(command):
            logger.info(f"RCON 接收消息: {data}")
            return data.strip()
    
    @property
    def _panel_config(self) -> PanelConfig:
        return self.config["panel"]

    @property
    def is_chat_available(self):
        _panel_config = self._panel_config
        return _panel_config is not None and _panel_config.url and _panel_config.apikey and _panel_config.instance_id and _panel_config.daemon_id

    @cached_property
    def _log_api_url(self):
        return f"{self._panel_config.url.rstrip('/')}/api/protected_instance/outputlog"

    @cached_property
    def _log_api_data(self):
        return {
            "apikey": self._panel_config.apikey,
            "remote_uuid": self._panel_config.daemon_id,
            "uuid": self._panel_config.instance_id,
            "size": 4096
        }

    _chat_ptn = re.compile(r"(?P<date>\d\d\d\d-\d\d-\d\d) (?P<time>\d\d:\d\d:\d\d) \[[A-Z]+\] (?P<content>.*)")

    _last_date = "0"
    _last_time = "0"

    def chat_gen(self, data: str):
        for line in data.splitlines():
            if m := self._chat_ptn.match(line):
                last_date, last_time = m.group('date'), m.group('time')
                if last_date <= self._last_date and last_time <= self._last_time:
                    continue
                self._last_date = last_date
                self._last_time = last_time
                content = CQunescape(Content(m.group('content')).brief)
                yield f"{last_time} {content}"

    async def get_chats(self):
        async with AsyncClient() as client:
            r = await client.get(self._log_api_url, params=self._log_api_data, timeout=10)
            r.raise_for_status()
            return [*self.chat_gen(r.json()["data"])]


_client: Client | None = None

@pluginConfig.on
def initFactorio(config:dict, bot):
    global _client
    _config: FactorioConfig | None = config.get("factorio")
    if _client is None:
        _client = Client(_config)
    else:
        _client.init(_config)

(Command("factorio").names("异星工厂", "异星")
 .opt(("-pl", "-玩家"), OPT.N, "玩家列表")
 .opt(("-e", "-进化"), OPT.N, "当前进化信息")
 .opt(("-t", "-时间"), OPT.N, "当前游戏时长")
)

@Events.onCmd("factorio")
async def factorio(pr:ParseResult):
    if not _client or not _client.is_inited:
        return ["失联了…"]

    msg: Message = pr.raw

    if pr["pl"]:
        return [await _client.send("/players")]
    if pr["e"]:
        return [await _client.send("/evolution")]
    if pr["t"]:
        return [await _client.send("/time")]
    
    command = pr.paramStr

    if not command.strip():
        if _client.is_chat_available:
            chats = await _client.get_chats()
            content = chain(("聊天记录",), chats)
            # return "\n".join(content)
            im_path = str2greyPng(content, fileName="factorio_chat.png", overwrite=True)
            return [Image(im_path, cache=False)]
        else:
            return ["聊天服务不可用…"]

    name = msg.getSrcCard() or str(msg.realSrc)
    command = f"[{name}] {CQunescape(Content(command).brief.lstrip('/'))}"
    # print(repr(command))
    try:
        return [await _client.send(command.lstrip("/"))]
    except InvalidResponse:
        return ["不支持这个指令！"]
    


