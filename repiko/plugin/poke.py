from repiko.core.bot import Bot
from repiko.core.constant import NoticeType,MessageType,EventNames,PostType
from repiko.core.log import logger
from repiko.msg.core import MCore
from repiko.msg.selector import NoticeSelector
from repiko.msg.data import Notice,Message
from repiko.msg.part import At
from repiko.msg.content import Content
from LSparser import Events,Command,ParseResult

# import asyncio
import yaml
from pathlib import Path
# from contextvars import ContextVar

@Events.on(NoticeSelector.getEventName())
async def onNotice(notice:Notice,bot:Bot):
    if notice.ntype == NoticeType.Notify and notice.subtype == "poke":
        await onPoke(notice,bot)

async def onPoke(notice:Notice,bot:Bot):
    if not bot.IsMe(notice.get("target_id")):
        return
    
    dst=notice["target_id"] # 被戳的
    if src:=notice.get("group_id"): # 群里戳
        mtype=MessageType.Group
    else:
        mtype=MessageType.Private
    msg=Message.build(".poke",dst,mtype)
    msg.realSrc=notice["user_id"] # 来自戳人者
    msg.src=src
    msg.postType=PostType.Message
    msg["self_id"]=bot.MYQQ
    msg.selector=[s for s in bot.selectors if s.isAccept(msg)][0]
    if src:
        msg["group_id"]=src
        msg["sender"]=await bot.GroupMemberInfo(msg.src,msg.realSrc,False)  
    else:
        msg["sender"]=await bot.QQInfo(msg.realSrc,False)
    # logger.debug(repr(msg))
    result=await bot.mc.AsyncResponse(msg)
    logger.debug(result)
    await bot.SendContents(msg.copy(srcAsDst=True),result)
    if msg.quickReply:
        rj=msg.replyJson
        reply:Content=rj["reply"]
        if rj.get("at_sender"):
            reply.insert(0,At(msg.realSrc))
        await bot.SendContents(msg.copy(srcAsDst=True),reply)


memberPokes:dict[int,str]={}
# meCount=ContextVar("meCount",default=0)
# meStack=asyncio.LifoQueue(maxsize=2)
pokeCount=0

Command("poke").names("戳")
Command("setpoke").names("pokeset")
Command("delpoke").names("pokedel")

@Events.onCmd("setpoke")
async def setme(pr:ParseResult):
    msg:Message=pr.raw
    qq=msg.realSrc
    name=msg.getSrcName()
    atMe=At(msg.realSrc).CQcode
    content=pr.paramStr.strip()
    if msg.hasAtMe:
        content=f"{atMe} {content}"
    memberPokes[qq]={ "name":name, "content":pr.paramStr }
    if not name or msg.mtype==MessageType.Group:
        name=atMe
    return [f"为 {name} 设置了 .poke"]

@Events.onCmd("delpoke")
async def setme(pr:ParseResult):
    msg:Message=pr.raw
    qq=msg.realSrc
    name=msg.getSrcName()
    content=memberPokes.pop(qq,None)
    if not name or msg.mtype==MessageType.Group:
        name=At(msg.realSrc).CQcode
    if not content:
        return [f"未找到 {name} 的 .poke"]
    return [f"为 {name} 删除了 .poke"]

@Events.onBeforeParse
async def before(pr:ParseResult,_):
    global pokeCount
    pokeCount+=1
    # meCount.set(meCount.get(0)+1)
    # await meStack.put_nowait(None)

@Events.onAfterParse
async def after(pr:ParseResult,_):
    global pokeCount
    pokeCount=0
    # meCount.set(meCount.get(1)-1)
    # await meStack.get_nowait()

@Events.onCmd("poke")
async def poke(pr:ParseResult):
    global pokeCount
    # mes=meCount.get()
    logger.debug(f"Poke: {pokeCount}")
    if pokeCount>=2: # 防止递归
        return ["请不要让我戳自己（"]
    msg:Message=pr.raw
    bot=msg.selector.bot
    default=[".at"]
    if not (content:=memberPokes.get(msg.realSrc,{}).get("content")):
        content=default
    newMsg=msg.copy()
    newMsg.content=content
    result=await bot._handleData(newMsg) # 几乎是从最外层重新处理消息
    if result:
        msg.quickReply=True
        msg._replyJson=result
    return []

path=Path("config/poke.yaml")

def initPoke():
    global memberPokes
    if path.exists():
        logger.info("载入 .poke 数据……")
        with path.open(encoding="utf-8") as f:
            memberPokes=yaml.safe_load(f)

def savePoke():
    logger.info("保存 .poke 数据……")
    with path.open("w",encoding="utf-8") as f:
        yaml.safe_dump(memberPokes,f,encoding="utf-8",allow_unicode=True)

@Events.on(EventNames.MsgCoreInit)
def coreInit(core:MCore):
    initPoke()

@Events.on(EventNames.Shutdown)
def botShutDown(bot:Bot):
    savePoke()
