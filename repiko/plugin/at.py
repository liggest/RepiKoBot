from LSparser import Events,Command,ParseResult,OPT

from repiko.core.bot import Bot
from repiko.core.constant import EventNames,MessageType
from repiko.msg.data import Message
from repiko.msg.part import Face,Reply,At
from repiko.msg.content import Content

import asyncio

@Events.on(EventNames.AtMe)
async def atMe(msg:Message,bot:Bot):
    # raw=msg
    if not isinstance(msg,str):
        content=msg.content.plainText
    if "是不是" in content:
        return "围观群众：是啊是啊"
    elif "生气了" in content:
        return "没有哦"
    elif "草" in content or "艹" in content:
        return msg.content
    elif "嘤" in content:
        return "我一拳打死一个嘤嘤怪"
    elif "哥" in content or "弟" in content:
        return "欧尼酱~"
    elif "姐" in content or "妹" in content:
        return "欧内酱~"
    elif content.strip()=="弱人工智能" or content.strip()=="鶸人工智能":
        return "你们阉太监也不会动人脑子！"
    elif "来一句" in content or "说一句" in content or "来句话" in content:
        return await bot.plugins["basic"].aword(None)
    else:
        return "不要碰我呀QwQ"

Command("at").names("@")

@Events.onCmd("at")
async def withdraw(pr:ParseResult):
    msg:Message=pr.raw
    atmsg=msg.copy()
    atmsg.content=pr.paramStr
    reply=await atMe(atmsg,msg.selector.bot)
    if msg.mtype==MessageType.Group:
        return [ Content(At(msg.realSrc),reply) ]
    return [reply]

scaredWords=[Face(55),Face(146),"多嘴","住口","住嘴","💣"] # 撤回关键字

Command("withdraw").names("撤回")\
    .opt(["-all","-both"],OPT.Not,"能撤回的话回复也撤回")

@Events.onCmd("withdraw")
async def withdraw(pr:ParseResult): # TODO 私聊暂不可用
    msg:Message=pr.raw
    if not (msg.isReply and msg.hasReplyMe):
        return ["回复我来让我撤回哦~"]
    await runaway(msg,msg.selector.bot,deleteBoth=pr["all"])

async def delayedDelete(bot:Bot,msgID:int,second:int=8):
    await asyncio.sleep(second)
    await bot.DeleteMsg(msgID)

async def runaway(msg:Message,bot:Bot,deleteBoth=False):
    if msg.replyDeleted:
        print("已经撤回过了")
        return
    reply:Reply=msg.content[0]
    await bot.DeleteMsg(reply.id)
    msg.replyDeleted=True
    if deleteBoth and msg.mtype==MessageType.Group:
        # print("也删这个")
        meInGroup=await bot.GroupMemberInfo(msg.src,bot.MYQQ)
        # print(meInGroup)
        myRole=meInGroup.get("role",None)
        if myRole=="owner" or myRole=="admin":
            asyncio.create_task(delayedDelete(bot,msg.id))
            # bot.AddBackTask(delayedDelete,bot,msg.id)

@Events.on(EventNames.ReplyMe)
async def replyMe(msg:Message,bot:Bot):
    content=msg.content
    # reply:Reply=content[0]
    for word in scaredWords:
        if word in content:
            await runaway(msg,bot,deleteBoth=True) # 能撤回的话都撤回
            break

