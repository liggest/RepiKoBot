
from typing import Iterable, SupportsIndex
from datetime import datetime, timedelta
from functools import cached_property
import json

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionMessage
from openai._types import NOT_GIVEN, NotGiven
import tiktoken
from mcp.types import CallToolRequestParams
from lxml.html import etree, fragment_fromstring, tostring
from lxml.etree import _Element

from chat.mcp import McpServers
from chat.log import logger
from chat.prompt import ToolPrompt, SystemPrompt

class LLM:

    def __init__(self, api_key: str, base_url: str):
        self.openai = AsyncOpenAI(api_key=api_key, base_url=base_url)
        # self.sessions = {}
        self.encoding: tiktoken.Encoding | None = None
    
    def get_encoding(self, model_name: str):
        if self.encoding:
            return self.encoding
        if model_name.startswith("gpt-4o"):
            self.encoding = tiktoken.get_encoding("o200k_base")
        else:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        return self.encoding

    # def new_session(self, session_id: str, model_name: str, system_prompt: str):
    #     session = Session(session_id, self, model_name, system_prompt)
    #     self.sessions[session_id] = session
    #     return session

    # def get_session(self, session_id: str):
    #     return self.sessions.get(session_id)

    async def _chat_call(self, model_name: str, messages: Iterable[ChatCompletionMessageParam], 
                         max_tokens: int | NotGiven = NOT_GIVEN, temperature: float | NotGiven = NOT_GIVEN):
        response = await self.openai.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False
        )
        return response.choices[0].message


class Session:
    def __init__(self, id: str, model_name: str, system_prompt: SystemPrompt | str, llm: LLM, mcp: McpServers, expire_time: timedelta | int = 60 * 60):
        self.id = id
        self.model_name = model_name
        self.llm = llm
        self.mcp = mcp
        self._raw_messages = Messages(system_prompt)
        # self.created_time: datetime = datetime.now()
        # self.last_response_time: datetime = datetime.now()
        if isinstance(expire_time, int):
            expire_time = timedelta(seconds=expire_time)
        self.expire_time = expire_time

    @property
    def create_time(self):
        return self._raw_messages.created_time
    
    @property
    def last_response_time(self):
        return self._raw_messages.last_response_time
    
    @property
    def is_expired(self):
        if self._raw_messages:
            return datetime.now() - self.last_response_time > self.expire_time
        return False  # no messages, not expired

    async def chat_once(self, prompt: str, 
                        max_tokens: int | NotGiven = NOT_GIVEN, temperature: float | NotGiven = NOT_GIVEN):
        logger.debug(f"Chatting with prompt:\n{prompt}")
        # self._raw_messages.append({"role": "user", "content": prompt})
        if self._raw_messages:
            self._raw_messages.last_dialogue.append(MessageUnit({"role": "user", "content": prompt}))

        response_message = await self.llm._chat_call(
            self.model_name,
            self._raw_messages.messages_gen(),
            max_tokens=max_tokens,
            temperature=temperature
        )

        # self.last_response_time = datetime.now()

        return response_message

    async def handle_tool_use(self, message: ChatCompletionMessage) -> list[str]:

        message = ReasoningMessage.model_construct(**message.model_dump(mode="json", exclude_none=True, exclude_unset=True, exclude_defaults=True))
        self._raw_messages.last_dialogue.append(MessageUnit(message))

        try:
            xml_message = message.content or ""
            # xml_message = "---".join(xml_message.split("</think>"))
            xml_message = xml_message.replace("</think>", "---")    # remove extra </think>
            root_element: _Element = etree.Element("root")  # <root>...</root>
            if message.reasoning_content:
                think_element = fragment_fromstring(message.reasoning_content, create_parent="think")  # <think>...</think>
                # root_element.insert(0, think_element)
                root_element.append(think_element)
                # xml_message = f"""<think>{message.reasoning_content}</think>\n{xml_message}"""
            # xml_message = f"<root>{xml_message}</root>"
            answer_element: _Element = fragment_fromstring(xml_message, create_parent="answer")  # <answer>...</answer>
            root_element.append(answer_element)

            logger.debug(f"Handling:\n{tostring(root_element, encoding='unicode')}")
            # tree = etree.fromstring(xml_message) 
            tree = root_element
        except (etree.XMLSyntaxError, etree.ParseError) as e:
            logger.error(error_msg := repr(e))
            return [ToolPrompt.error(tool_name=None, error=error_msg)]
        
        tool_use_elements: list[_Element] = tree.findall(".//tool_use")
        tool_use_results = []
        for tool_use in tool_use_elements:
            try:
                tool_use_info = self.parse_tool_use(tool_use)
            except Exception as e:
                logger.error(error_msg := repr(e))
                tool_name = None
                if (name_node := tool_use.find("name")) is not None and name_node.text:
                    tool_name = name_node.text
                tool_use_results.append(ToolPrompt.error(tool_name, error_msg))
                continue
        
            if tool_use_info:
                try:
                    result = await self.mcp.call_tool(tool_use_info.name, tool_use_info.arguments)
                    tool_use_results.append(ToolPrompt.result(tool_use_info.name, result))
                except Exception as e:
                    logger.error(error_msg := repr(e))
                    tool_use_results.append(ToolPrompt.error(tool_use_info.name,error_msg))
        
        return tool_use_results
        
    def parse_tool_use(self, tool_node):
        name_node = tool_node.find("name")
        if name_node is None:
            raise ValueError("Tool name not found")
        tool_name = name_node.text
        if not tool_name:
            raise ValueError("Tool name is empty")
        arguments = None
        arguments_node = tool_node.find("arguments")
        if arguments_node is not None and arguments_node.text:
            arguments = json.loads(arguments_node.text)
        return CallToolRequestParams(name=tool_name, arguments=arguments)

    async def chat(self, prompt: str, 
                   max_tokens: int | NotGiven = NOT_GIVEN, temperature: float | NotGiven = NOT_GIVEN):
        self._raw_messages.append(Dialogue())
        try:
            response = await self.chat_once(prompt, max_tokens, temperature)
            # tool_use_count = 0
            while tool_use_results := await self.handle_tool_use(response):
                tool_response_prompt = "\n".join(tool_use_results)
                response = await self.chat_once(tool_response_prompt, max_tokens, temperature)
        finally:
            if not self._raw_messages.last_dialogue:
                self._raw_messages.pop()
        
        return response
    
    def rotate(self, max_tokens: int):
        encoding = self.llm.get_encoding(self.model_name)
        
        total_tokens = self._raw_messages.count_tokens(encoding)
        if total_tokens <= max_tokens:
            return
        
        remain_tokens = total_tokens
        for idx, dialogue in enumerate(self._raw_messages):
            remain_tokens -= dialogue.count_tokens(encoding)
            if remain_tokens <= max_tokens:
                break
        
        self._raw_messages: Messages = self._raw_messages[idx:]

class ReasoningMessage(ChatCompletionMessage):
    reasoning_content: str | None = None
    """The contents of the reasoning."""

    @cached_property
    def message_param(self) -> ChatCompletionMessageParam:
        return {"role": self.role, "content": self.content}

class MessageUnit:
    def __init__(self, content: ChatCompletionMessageParam | ReasoningMessage, 
                 create_time: datetime | None = None, tokens: int = 0):
        self.content = content
        self.create_time = create_time or datetime.now()
        self.tokens = tokens or 0

    def count_tokens(self, encoding: tiktoken.Encoding):
        if self.tokens:
            return self.tokens
        self.tokens = len(encoding.encode(self.as_param()["content"])) + 4  # role
        return self.tokens

    def as_param(self) -> ChatCompletionMessageParam:
        if isinstance(self.content, ReasoningMessage):
            return self.content.message_param
        return self.content

class Dialogue(list[MessageUnit]):
    def __init__(self, messages: Iterable[MessageUnit] | None = None):
        if messages:
            super().__init__(messages)
        self.tokens = 0

    @property
    def create_time(self):
        if self:
            return self[0].create_time
        raise AttributeError("Dialogue is empty")

    @property
    def last_response_time(self):
        if self:
            return self[-1].create_time
        raise AttributeError("Dialogue is empty")

    @property
    def pair(self):
        if self:
            yield self[0]
        if len(self) >= 2:
            yield self[-1]


    def messages_gen(self):
        for message in self:
            yield message.as_param()

    def count_tokens(self, encoding: tiktoken.Encoding):
        if self.tokens:
            return self.tokens
        self.tokens = sum(message.count_tokens(encoding) for message in self)
        return self.tokens

class Messages(list[Dialogue]):
    def __init__(self, system_prompt: SystemPrompt | str, items: Iterable[Dialogue] = None):
        if items:
            super().__init__(items)
        else:
            super().__init__()
        if isinstance(system_prompt, str):
            system_prompt = SystemPrompt(str)
        self._system_prompt = system_prompt
    
    def __getitem__(self, idx: SupportsIndex | slice):
        if isinstance(idx, slice):
            return self.__class__(self._system_prompt, items=super().__getitem__(idx))
        return super().__getitem__(idx)

    @property
    def _system_message(self):
        return self._system_prompt.as_param()

    @property
    def created_time(self):
        if self:
            return self[0].create_time
        raise AttributeError("Message list is empty")

    @property
    def last_response_time(self):
        if self:
            return self[-1].last_response_time
        raise AttributeError("Message list is empty")

    @property
    def last_dialogue(self) -> Dialogue:
        if not self:
            self.append(Dialogue())
        return self[-1]

    def messages_gen(self, with_system = True):
        if with_system:
            yield self._system_message
        for dialogue in self:
            yield from dialogue.messages_gen()

    def count_tokens(self, encoding: tiktoken.Encoding):
        return sum(dialogue.count_tokens(encoding) for dialogue in self)


# class _Messages(list[ChatCompletionMessageParam | ReasoningMessage | "Messages"]):
#     def __init__(self, system_message: ChatCompletionMessageParam | None = None):
#         super().__init__()
#         self._system_message = system_message
    
#     def messages_gen(self, with_system = True):
#         if with_system and self._system_message:
#             yield self._system_message
#         for message in self:
#             match message:
#                 case ReasoningMessage():
#                     yield message.message_param
#                 case Messages():
#                     yield from message.messages_gen()
#                 case _:
#                     yield message
