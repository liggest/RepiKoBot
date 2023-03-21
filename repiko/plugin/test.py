from LSparser import *
from LSparser.event import EventNames
from LSparser.command.parser import CommandState
from repiko.msg.part import Record,TTS
from repiko.msg.data import Message

Command("-test1")
Command("-test2")
Command("update")

@Events.onCmd("test1")
def test1(_):
    return [Record("https://cdn.jsdelivr.net/gh/blacktunes/hiiro-button@master/public/voices/baba.mp3",cache=False)]

@Events.onCmd("test2")
def test2(_):
    return [TTS("聚集的祈愿将成为新生的闪耀之星，化作光芒闪耀的道路吧！\n同调召唤，飞翔吧，星尘龙！")]

@Events.onCmd("update")
def update(pr:ParseResult):
    msg:Message=pr.raw
    return [msg.selector.bot.update]

Command("wtf").names("wtf?","cmd","cmd?")

@Events.onCmd("wtf")
async def wtf(pr:ParseResult):
    cmd=pr.paramStr
    parser=pr.parser
    if not cmd.startswith(tuple(parser.core.potentialPrefix)):
        cmd=f".{cmd}" # 默认用 . 做前缀
    npr=parser.getCommand(cmd)
    # parser.core.EM.send(EventNames.BeforeParse,npr,parser)
    await parser.core.EM.asyncSend(EventNames.BeforeParse,npr,parser)
    if npr and npr.state==CommandState.DefinedCommand: # 不能包括 WrongCommand
        npr=parser.parse(npr)
        result=[pr2str(npr)]
    elif not npr.isCommand():
        #各种事件
        await parser.core.EM.asyncSend(EventNames.NotCmd,npr,parser)
        # parser.core.EM.send(EventNames.NotCmd,npr,parser)
        result=["似乎不是指令呀"]
    elif not npr.isDefinedCommand():
        # parser.core.EM.send(EventNames.UndefinedCmd,npr,parser)
        await parser.core.EM.asyncSend(EventNames.UndefinedCmd,npr,parser)
        result=[f"是没见过的指令诶\n{pr2str(npr)}"]
    elif npr.isWrongType():
        # parser.core.EM.send(EventNames.WrongCmdType,npr,parser)
        await parser.core.EM.asyncSend(EventNames.WrongCmdType,npr,parser)
        result=["\n".join([
            "指令类型错误",
            {pr2str(npr)},
            "该指令支持的类型如下",
            " ".join(npr._cmd.typelist)
        ])]
    # parser.core.EM.send(EventNames.AfterParse,npr,parser)
    await parser.core.EM.asyncSend(EventNames.AfterParse,npr,parser)
    return result


def pr2str(pr:ParseResult):
    result=[
        str(pr.raw),
        f"类型：{pr.type or '未知'}",
        f"指令：{pr.command or '未知'}",
        f"参数：{pr.params}"
    ]
    if pr.hasOpt():
        result.extend(f"{k}: {v}" for k,v in pr.args.items())
    return "\n".join(result).strip()
