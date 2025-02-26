import asyncio
from pathlib import Path

from repiko.msg.part import Image
from repiko.msg.data import Message
from repiko.msg.util import CQunescapeComma
from repiko.module.helper import RpkHelper as CommandHelper, renderHelpToml

from LSparser import Command, Events, ParseResult, CommandCore, OPT
from LSparser.event import EventNames
from LSparser.command.parser import CommandState

Command("help").names("?","？").opt("-p",OPT.M,"页数").opt(["-text", "-t"],OPT.N,"经典文本帮助")
# .opt("-im",OPT.N,"以图片发送")

CommandHelper.lineLimit=20

@Events.onCmd("help")
async def helpinfo(pr:ParseResult):
    if f"{pr.type}{pr.command}" in ("!?","！？"):
        return [] # !? 和 ！？ 不触发

    root = Path("help")
    core = pr.parser.core
    if core.name != CommandCore.default:
        root = root / core.name
    h = CommandHelper(root, core)
    if not pr["text"]:
        result = h.getHelpToml(pr.params)
        if result:
            return [Image(
                await asyncio.to_thread(renderHelpToml,result)
            )]
        else:
            pr.args["text"]=True
    if pr["text"]:
        page = pr.getToType("p", 1, int)
        result = h.getHelp(pr.params, page)
        if result:
            return [CQunescapeComma(result)]
    return ["是没见过的帮助呢"]

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
