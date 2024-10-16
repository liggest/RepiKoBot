from LSparser import Command, Events, ParseResult, CommandParser, OPT
from LSparser.event import EventNames
from LSparser.command.parser import CommandState
from repiko.core.log import logger
from repiko.core.api import ApiError
from repiko.msg.content import Content
from repiko.msg.part import Record, TTS, Node, Forward
from repiko.msg.data import Message

Command("-test1")


@Events.onCmd("test1")
def test1(_):
    return [Record("https://cdn.jsdelivr.net/gh/blacktunes/hiiro-button@master/public/voices/baba.mp3",cache=False)]

Command("-test2")
@Events.onCmd("test2")
def test2(_):
    return [TTS("聚集的祈愿将成为新生的闪耀之星，化作光芒闪耀的道路吧！\n同调召唤，飞翔吧，星尘龙！")]

Command("-test3")
@Events.onCmd("test3")
def test3(pr: ParseResult):
    msg: Message = pr.raw
    return [Node(qq=msg.selector.bot.MYQQ, content="这是假的！")]

Command("-test4")
@Events.onCmd("test4")
def test4(pr: ParseResult):
    msg: Message = pr.raw
    return [Node.fromMsgID(msg.id)]

Command("-test5")
@Events.onCmd("test5")
def test5(pr: ParseResult):
    msg: Message = pr.raw
    return [Node.fromMsg(msg, content="这是假的！")]

Command("-unpack")
@Events.onCmd("unpack")
async def unpack(pr: ParseResult):
    msg: Message = pr.raw
    content = Content(pr.paramStr)
    if Forward in content:
        forward: Forward = content[Forward][0]
        fwds = await msg.selector.bot.GetForward(forward.id)
        return [fwd.content for fwd in fwds]
    return ["似乎不是合并转发"]

Command("update")
@Events.onCmd("update")
def update(pr: ParseResult):
    msg: Message = pr.raw
    return [msg.selector.bot.update]

Command("wtf").names("wtf?", "cmd", "cmd?")
@Events.onCmd("wtf")
async def wtf(pr: ParseResult):
    cmd = pr.paramStr
    parser = pr.parser
    if not cmd.startswith(tuple(parser.core.potentialPrefix)):
        cmd = f".{cmd}"  # 默认用 . 做前缀
    npr = parser.getCommand(cmd)
    # parser.core.EM.send(EventNames.BeforeParse,npr,parser)
    await parser.core.EM.asyncSend(EventNames.BeforeParse, npr, parser)
    if npr and npr.state == CommandState.DefinedCommand:  # 不能包括 WrongCommand
        npr = parser.parse(npr)
        result = [pr2str(npr)]
    elif not npr.isCommand():
        # 各种事件
        await parser.core.EM.asyncSend(EventNames.NotCmd, npr, parser)
        # parser.core.EM.send(EventNames.NotCmd,npr,parser)
        result = ["似乎不是指令呀"]
    elif not npr.isDefinedCommand():
        # parser.core.EM.send(EventNames.UndefinedCmd,npr,parser)
        await parser.core.EM.asyncSend(EventNames.UndefinedCmd, npr, parser)
        result = [f"是没见过的指令诶\n{pr2str(npr)}"]
    elif npr.isWrongType():
        # parser.core.EM.send(EventNames.WrongCmdType,npr,parser)
        await parser.core.EM.asyncSend(EventNames.WrongCmdType, npr, parser)
        result=["\n".join([
            "指令类型错误",
            pr2str(npr),
            "该指令支持的类型如下",
            " ".join(npr._cmd.typelist)
        ])]
    # parser.core.EM.send(EventNames.AfterParse,npr,parser)
    await parser.core.EM.asyncSend(EventNames.AfterParse, npr, parser)
    return result


def pr2str(pr: ParseResult):
    result = [
        str(pr.raw),
        f"类型：{repr(pr.type) if pr.type else '未知'}",
        f"指令：{repr(pr.command) if pr.command else '未知'}",
        f"参数：{repr(pr.params)}"
    ]
    if pr.hasOpt():
        result.extend(f"{k}: {v}" for k, v in pr.args.items())
    return "\n".join(result).strip()

Command("-error").opt("-api", OPT.N, "ApiError")
@Events.onCmd("error")
async def error(pr: ParseResult):
    if pr["api"]:
        raise ApiError({"retcode": -1, "msg": "test"})
    else:
        from httpx import TimeoutException
        raise TimeoutException("test")

@Events.onExecuteError
async def pasteErrorEmoji(pr: ParseResult, parser: CommandParser, e: Exception):
    msg: Message = pr.raw
    if not isinstance(e, ApiError):
        await msg.selector.bot.PasteEmoji(msg.id, 128557)  # 大哭
    else:
        try:
            await msg.selector.bot.PasteEmoji(msg.id, 128560)  # 紧张
        except ApiError as e:
            logger.error("表情都贴不上了！")
            raise e
