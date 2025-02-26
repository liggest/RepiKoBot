from LSparser import Command, Events, ParseResult, CommandParser, OPT
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
    if not msg.id:
        logger.warning("无法为没有 id 的消息贴表情")
        return
    try:
        if not isinstance(e, ApiError):
            await msg.selector.bot.PasteEmoji(msg.id, 128557)  # 大哭
        else:
            await msg.selector.bot.PasteEmoji(msg.id, 128560)  # 紧张
    except ApiError as e:
        logger.error("表情都贴不上了！")
        raise e
