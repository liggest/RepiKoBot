
import asyncio
from contextlib import AsyncExitStack
from datetime import timedelta

from typing import AsyncContextManager

from mcp import ClientSession, Tool
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.websocket import websocket_client

from chat.log import logger

class Server:

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self._client_context: AsyncContextManager | None = None
        self._session: ClientSession | None = None
        self._tools: dict[str, Tool] = {}
        self.is_inited = False

    async def __aenter__(self):
        try:
            await self._init()
        except Exception as e:
            logger.error(f"MCP {self.name!r} failed to init: {e!r}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.is_inited = False
        if self._session:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
        if self._client_context:
            await self._client_context.__aexit__(exc_type, exc_val, exc_tb)
        self._session = None
        self._client_context = None
        self._tools.clear()
    
    async def _init(self):
        if self.config.get("disabled"):
            logger.info(f"MCP {self.name!r} is disabled, skipping initialization")
            return
        transport_type = self.config.get("transportType")
        if transport_type == "stdio" or "command" in self.config:
            self._client_context = stdio_client(StdioServerParameters(**self.config))
        elif transport_type == "sse" or "url" in self.config:
            self._client_context = sse_client(**self.config)
        elif transport_type == "websocket":
            self._client_context = websocket_client(**self.config)
        read, write = await self._client_context.__aenter__()
        self._session = ClientSession(read, write, read_timeout_seconds=timedelta(seconds=10))
        await self._session.__aenter__()
        await self._session.initialize()
        self.is_inited = True

    async def _update_tools(self) -> dict[str, Tool]:
        if self._session is None:
            return self._tools
        tools = (await self._session.list_tools()).tools
        self._tools = { tool.name: tool for tool in tools }
        logger.info(f"MCP {self.name!r} inited with {len(self._tools)} tools")
        return self._tools

    async def call_tool(self, tool_name: str, arguments: dict[str, str] | None = None):
        logger.info(f"Calling tool {tool_name!r} on server {self.name!r} with arguments {arguments!r}")
        return await self._session.call_tool(tool_name, arguments)

class McpServers:

    def __init__(self, config: dict[str, dict]):
        self.servers = [Server(server_name, server_config) for server_name, server_config in config.items()]
        self.tool2server: dict[str, Server] = {}
        self._server_contexts: AsyncExitStack | None = None

        self._ready = asyncio.Event()
        self._end = asyncio.Event()

    async def __aenter__(self):
        logger.info("MCP Servers initing...")
        self._server_contexts = await AsyncExitStack().__aenter__()
        for server in self.servers:
            await self._server_contexts.enter_async_context(server)
        await self.init_tools()
        logger.info("MCP Servers inited")
        # logger.debug(self.tool2server.keys())
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._server_contexts.__aexit__(exc_type, exc_val, exc_tb)
        self._server_contexts = None
        self._ready.clear()
        self._end.clear()

    @property
    async def is_ready(self):
        await self._ready.wait()
        return True
    
    def wrap_tool_name(self, tool_name: str, server: Server) -> str:
        return f"{server.name}::{tool_name}"

    def unwrap_tool_name(self, tool_name: str, server: Server) -> str:
        return tool_name.removeprefix(f"{server.name}::")

    async def _update_tools(self, server: Server):
        tools = await server._update_tools()
        for tool_name in tools:
            if tool_name not in self.tool2server:
                self.tool2server[tool_name] = server
            else:
                tool_name = self.wrap_tool_name(tool_name, server)
                # if tool_name in self.tool2server:
                #     raise ValueError(f"Tool {tool_name} already exists!")
                self.tool2server[tool_name] = server
    
    # async def _enter_and_update_tools(self, server: Server):
    #     # await self._server_contexts.enter_async_context(server)
    #     await self._update_tools(server)

    async def init_tools(self):
        self.tool2server.clear()
        try:
            await asyncio.gather(
                *(self._update_tools(server) for server in self.servers)
            )
        except Exception as e:
            logger.error(f"Error initializing MCP servers: {e}")
        return self.tool2server
        
    async def call_tool(self, tool_name: str, arguments: dict[str, str] | None = None):
        if server := self.tool2server.get(tool_name):
            return await server.call_tool(self.unwrap_tool_name(tool_name, server), arguments)
        raise ValueError(f"Tool {tool_name!r} not found")

    async def run(self):
        async with self:
            self._ready.set()
            await self._end.wait()
            logger.info("MCP Servers ended")
            