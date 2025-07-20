from __future__ import annotations
from typing import TYPE_CHECKING
from functools import cached_property

if TYPE_CHECKING:
    from chat.mcp import McpServers

from mcp.types import Tool, CallToolResult
from mcp.types import TextContent, ImageContent, EmbeddedResource, TextResourceContents, BlobResourceContents

class SystemPrompt:

    def __init__(self, content: str):
        self.content = content

    def gen(self):
        yield self.content

    def build(self):
        return "\n".join(self.gen())

    @cached_property
    def prompt(self):
        return self.build()
    
    def __str__(self):
        return self.prompt

    def as_param(self):
        return {"role": "system", "content": self.prompt}

class McpSystemPrompt(SystemPrompt):

    ToolUse = """当前环境中，你在解答问题时可以调用一组特定的工具，工具执行结果将通过用户响应返回。请分步骤完成任务，基于前一步的结果决定下一步调用何种工具。

## 工具调用格式规范

采用 XML 标签声明对工具的调用。工具名称包裹在 <name> 标签中，参数封装在 <arguments> 标签中。具体如下：

<tool_use>
  <name>{工具名称}</name>
  <arguments>{JSON参数}</arguments>
</tool_use>

工具名称需与想要调用的工具完全对应，参数需以 JSON 对象形式提供。例如：

<tool_use>
  <name>python_interpreter</name>
  <arguments>{"code": "5 + 3 + 1294.678"}</arguments>
</tool_use>

系统将以用户的身份返回工具执行结果，格式如下：

<tool_use_result>
<name>{工具名称}</name>
<result>{执行结果}</result>
</tool_use_result>

执行结果为字符串格式，但也可表示文件或其他类型的输出，该结果可作为后续步骤的输入。

如果解析或执行工具调用时出错，将返回错误信息（大多为 Python 中的 Exception 对象），格式如下：

<tool_use_result>
<name>{工具名称}</name>
<error>{错误信息}</error>
</tool_use_result>

遇到错误时，请尝试修正错误并重新调用工具，或改用其它工具代替。如果无法解决错误，请如实向用户报告当前情况，并尽可能直接解答用户提出的问题。

可以使用多个并列的 <tool_use> 标签一次性调用至多 10 个工具。

请不要自行用 <tool_use_result> 标签提供工具调用的结果，这样做会影响到工具的解析和使用。如果在调用工具前已经能把握其结果，请直接解答用户提出的问题。

请严格遵守此格式规范以确保调用被正确解析和执行。

## 工具调用示例
以下是一些示例，使用了假想的工具：

---
User: 生成一张 document.pdf 中最年长的人的画像

Assistant: <tool_use>
  <name>document_qa</name>
  <arguments>{"document": "document.pdf", "question": "文档中最年长的人是谁？"}</arguments>
</tool_use>

User: <tool_use_result>
  <name>document_qa</name>
  <result>张三，55 岁，一位内蒙古通辽市的技术工人。</result>
</tool_use_result>

Assistant: <tool_use>
  <name>image_generator</name>
  <arguments>{"prompt": "一张张三的肖像。他是一名 55 岁的技术工人，来自内蒙古。"}</arguments>
</tool_use>

User: <tool_use_result>
  <name>image_generator</name>
  <result>image.png</result>
</tool_use_result>

Assistant: 这是生成的画像：image.png。

---
User: 5 + 3 + 1294.678 等于多少？

Assistant: <tool_use>
  <name>python_interpreter</name>
  <arguments>{"code": "5 + 3 + 1294.678"}</arguments>
</tool_use>

User: <tool_use_result>
  <name>python_interpreter</name>
  <result>1302.678</result>
</tool_use_result>

Assistant: 等于 1302.678。

---
User: 广州和上海哪个城市人口更多？

Assistant: <tool_use>
  <name>search</name>
  <arguments>{"query": "Population Guangzhou"}</arguments>
</tool_use>

<tool_use>
  <name>search</name>
  <arguments>{"query": "Population Shanghai"}</arguments>
</tool_use>

User: <tool_use_result>
  <name>search</name>
  <result>截至 2021 年，广州人口为 1500 万。</result>
</tool_use_result>

<tool_use_result>
  <name>search</name>
  <result>2600万（2019年）</result>
</tool_use_result>

Assistant: 上海人口为 2600 万，而广州人口为 1500 万，因此上海人口更多。
"""

    def __init__(self, mcp: McpServers, identity = ""):
        self.mcp = mcp
        if identity:
            self.identity = identity
    
    @classmethod
    def tool(cls, tool: Tool, tool_name: str = ""):
        return f"""<tool>
    <name>{tool_name or tool.name}</name>
    <description>{tool.description}</description>
    <argument_schema>{tool.inputSchema}</argument_schema>
</tool>"""

    def tools_gen(self):
        for tool_name, server in self.mcp.tool2server.items():
            if tool := server._tools.get(self.mcp.unwrap_tool_name(tool_name, server)):
                yield self.tool(tool, tool_name)

    def tools(self):
        return "\n".join(self.tools_gen())

    def tool_list(self):
        return f"""## 可用工具列表

上述示例中的工具可能不存在，实际可用的工具如下：

```xml
{self.tools()}
```"""

    ToolUseRules = """## 工具调用的核心原则

请始终遵守以下规则：
1. 请使用正确的参数格式，参数值必须使用实际值而非变量名。
2. 仅在必要时调用工具。如无需额外信息，请自主解决问题。
3. 不需要调用工具时请直接回答问题。
4. 不要用完全相同的参数重复调用同一工具。
5. 请像上述示例中那样使用 XML 标签，不要用其他格式。"""

    identity = """你是一个 QQ 聊天机器人，负责与其它 QQ 用户聊天（私聊、群聊），解答他们的问题。
    
    解答问题时，请尽量使用 Markdown 格式向用户呈现最终结果。"""

    def background_info(self):
        return f"""## 背景信息

{self.identity}

现在开始！成功完成任务将获得 100 万元奖励。"""

    def gen(self):
        yield self.ToolUse
        yield self.tool_list()
        yield self.ToolUseRules
        yield self.background_info()

class ToolPrompt:

    @classmethod
    def result_content_gen(cls, result: CallToolResult):
        for content in result.content:
            match content:
                case TextContent(text=text):
                    yield text
                case ImageContent(mimeType=mime_type, data=data):
                    yield f"<image mime_type={mime_type!r}>{data}</image>"
                case EmbeddedResource(resource=resource):
                    if isinstance(resource, TextResourceContents):
                        yield resource.text
                    elif isinstance(resource, BlobResourceContents):
                        yield resource.blob

    @classmethod
    def result_gen(cls, tool_name: str | None, result: CallToolResult | None, error: str | None = None):
        yield "<tool_use_result>"
        if tool_name:
            yield f"<name>{tool_name}</name>"
        if result:
            content = "\n".join(cls.result_content_gen(result)) or "None"
            if result.isError:
                yield f"<error>{content}</error>"
            else:
                yield f"<result>{content}</result>"
        if error:
            yield f"<error>{error}</error>"
        yield "</tool_use_result>"

    @classmethod
    def result(cls, tool_name: str, result: CallToolResult | None):
        return "\n".join(cls.result_gen(tool_name, result))

    @classmethod
    def error(cls, tool_name: str | None, error: str):
        return "\n".join(cls.result_gen(tool_name, result=None, error=error))
