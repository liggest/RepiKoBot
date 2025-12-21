
import asyncio
import inspect
from typing import Callable, Awaitable
from functools import cached_property, update_wrapper

from openai.types.chat import ChatCompletionFunctionToolParam, ChatCompletionToolChoiceOptionParam

from mcp.types import CallToolResult
from mcp.server.fastmcp.utilities.func_metadata import func_metadata

from chat.mcp import McpServers, Server
from chat.log import logger

ToolResult = str | CallToolResult

class CallableTool:

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.schema: dict | None = None
        self._to_call: Callable[..., Awaitable[ToolResult]] | None = None
        self.enable = True
        # self.strict = False

    @classmethod
    def from_function(cls, func: Callable[..., Awaitable[ToolResult] | ToolResult], name: str | None = None, description: str | None = None):
        if not inspect.isfunction(func):
            func = func.__call__
        func_name = name or func.__name__
        func_desc = description or func.__doc__ or ""

        tool = cls(name=func_name, description=func_desc)
        metadata = func_metadata(func)
        tool.schema = metadata.arg_model.model_json_schema(by_alias=True)
        tool._to_call = func

        if not asyncio.iscoroutinefunction(func):
            async def _async_wrapper(*args, **kw):
                return func(*args, **kw)
            
            update_wrapper(_async_wrapper, func)
            tool._to_call = _async_wrapper
        
        return tool

    @classmethod
    def from_mcp(cls, tool_name: str, server: Server, mcp: McpServers):
        if not server.is_inited:
            raise ValueError("MCP Server is not inited")
        
        tool_name_in_server = mcp.unwrap_tool_name(tool_name, server)
        mcp_tool = server._tools[tool_name_in_server]
        tool = cls(name=tool_name, description=mcp_tool.description)
        tool.schema = mcp_tool.inputSchema

        async def _call_tool(**arguments):
            return await server.call_tool(tool_name_in_server, arguments)

        tool._to_call = _call_tool
        return tool

    @cached_property
    def param(self) -> ChatCompletionFunctionToolParam:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema or {},
                # "strict": self.strict
            }
        }

    def as_param(self) -> ChatCompletionFunctionToolParam:
        return self.param

    async def call(self, arguments: dict):
        if self._to_call is None:
            raise ValueError(f"Tool {self.name!r} is not callable !?")
        
        return await self._to_call(**arguments)

class ToolManager:
    
    def __init__(self, mcp: McpServers | None = None):
        self.mcp = mcp
        self.tools: dict[str, CallableTool] = {}
        self.mcp_tools: dict[str, CallableTool] = {}
        self._mcp_tools_inited = False
        self.tool_choice: ChatCompletionToolChoiceOptionParam = "auto"  # let the model decide whether to use tools

    def callable_tools_gen(self):
        yield from self.tools.values()
        if self.mcp:
            yield from self.mcp_tools.values()

    def tools_gen(self):
        for tool in self.callable_tools_gen():
            if tool.enable:
                yield tool.as_param()

    def update_mcp_tools(self):
        if not self.mcp:
            return
        
        self.mcp_tools = {
            tool_name: CallableTool.from_mcp(tool_name, server, self.mcp) 
            for tool_name, server in self.mcp.tool2server.items()
        }

    def add_tool(
        self,
        fn: Callable = None,
        /,
        name: str | None = None,
        description: str | None = None,
    ):
        if fn is None:
            def wrapper(func: Callable):
                return self.add_tool(func, name=name, description=description)
            
            return wrapper

        tool = CallableTool.from_function(fn, name=name, description=description)

        if tool.name in self.tools:
            raise ValueError(f"Tool {tool.name!r} already exists")
            
        self.tools[tool.name] = tool
        logger.info(f"ToolManager added tool {tool.name!r}")
        return fn


    async def call_tool(self, tool_name: str, arguments: dict):
        if (tool := self.tools.get(tool_name)) or (tool := self.mcp_tools.get(tool_name)):
            return await tool.call(arguments)
        
        raise ValueError(f"Tool {tool_name!r} not found")
