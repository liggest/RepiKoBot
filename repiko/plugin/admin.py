from repiko.core.bot import Bot
from repiko.core.constant import EventNames,MessageType
# from repiko.msg.core import MCore
from repiko.msg.data import Message,Request
from repiko.msg.selector import RequestSelector
# from repiko.msg.message import Message
from repiko.msg.content import Content
from repiko.msg.util import CQunescapeComma

from LSparser import *

import typing
import functools
import asyncio

broadcastPreset={}
def loadBroadcastPreset(bot:Bot):
    global broadcastPreset
    for k,v in bot.config["broadcast"].items():
        if isinstance(v,list):
            v={"group":v}   # 默认群广播
        elif isinstance(v,int):
            v={"group":[v]} # 默认群广播
        if v:
            broadcastPreset[k]=v
    broadcastPreset["admin"]={ "private":[ q for q in bot.AdminQQ if not bot.IsMe(q) ] }

def fillQQs(qq:typing.Union[typing.List[str],dict,str,None],qqs:dict,key=MessageType.Group):
    if qq:
        if isinstance(qq,str): 
            if qq.isdigit(): #单个qq号
                qq=[int(qq)]
            else:
                return qqs #不是qq号
        elif isinstance(qq,list): #qq号列表
            qq=[ int(q) for q in qq if isinstance(q,int) or q.isdigit() ]
        elif isinstance(qq,dict): #qq号字典，一般来自 preset
            for k,v in qq.items():
                qqs=fillQQs(v,qqs,k)
            return qqs
        if key in qqs:
            qqs[key]+=qq
        else:
            qqs[key]=qq
    return qqs

AdminMode=False
# ModeText={False:"OFF",True:"ON"}
ModeText=["OFF","ON"] # False:OFF True:ON
# ModeVal ={"OFF":False,"ON":True}

with CommandCore(name="admin") as core:
    core.commandPrefix=["-","!","！"]
    core.potentialPrefix=set(core.commandPrefix)

    Command("admin")
    Command("broadcast").opt(["--qq","-qq"],OPT.M,"QQ号").opt(["--group","-group"],OPT.M,"群号").opt(["--preset","-preset"],OPT.M,"预设发送集合")

    # AdminOnlys
    Command("debug")
    Command("status").names("version")
    # Command("clean")
    # Command("restart").opt(["-time","-t"],OPT.M,"重启延迟（毫秒）") #重启不知道为啥不好使
    Command("reload")

    @Events.onBeforeParse
    def check(pr:ParseResult, cp:CommandParser):
        # print(pr)
        # print(pr.state)
        msg:Message=pr.raw
        bot:Bot=pr.parserData["mc"].bot
        if bot and not msg.realSrc in bot.AdminQQ:
            pr.state=ParseResult.CommandState.NotCommand # 不再继续解析

    def AdminOnly(func):
        """
            只在 AdminMode 下或从 admin 指令内部触发时执行函数
        """
        @functools.wraps(func)
        async def wrapper(pr:ParseResult,*args,**kw):
            if AdminMode or pr.dataKW.get("fromAdmin") is True:
                if asyncio.iscoroutinefunction(func):
                    return await func(pr,*args,**kw)
                else:
                    return func(pr,*args,**kw)
            return []
        return wrapper

    @Events.onCmd("admin")
    async def admin(pr:ParseResult):
        global AdminMode
        if not pr.params:
            pr.params.append( ModeText[not AdminMode] ) # 无参数时默认切换 AdminMode
        sub:str=pr.params[0]
        subUp=sub.upper()
        if subUp in ModeText: # ON/OFF
            AdminMode= subUp==ModeText[True] # True/False
            return ["Admin Mode:"+ModeText[AdminMode]]
        else:
            cmd=f"!{pr.paramStr}"
            msg:Message=pr.raw
            msg=msg.copy()
            msg.content=cmd
            apr=await pr.parser.asyncTryParse(msg,fromAdmin=True) # 触发其它 AdminOnly 指令
            result=[]
            for l in apr.output:
                result+=l
            return result
    
    @Events.onCmd("broadcast")
    async def broadcast(pr:ParseResult):
        bot:Bot=pr.parserData["mc"].bot
        content=None
        if pr.params:
            content=pr.paramStr
            if content.strip()=="update":
                content=bot.update
        qqs={}
        qqs=fillQQs(pr["qq"],qqs,MessageType.Private)
        qqs=fillQQs(pr["group"],qqs,MessageType.Group)
        presetName=pr["preset"]
        if presetName:
            if isinstance(presetName,str):
                presetName=[presetName]
            for psn in presetName:
                ps=broadcastPreset.get(psn)
                if ps:
                    qqs=fillQQs(ps,qqs)
        if qqs:
            if content:
                await bot.Broadcast(qqs,Message.build(content))
            num=0
            result=""
            # result="广播如下：\n"
            for k,v in qqs.items():
                result+=f"{k}: {', '.join([ str(qq) for qq in v ])}\n"
                num+=len(v)
            if content:
                result+=f"向共计 {num} 处广播了消息"
            else:
                result+=f"预计向共计 {num} 处广播消息"
            return [result]
        return ["我不知道要发给谁"]

    @Events.onCmd("debug")
    @AdminOnly
    def debug(pr:ParseResult):
        bot:Bot=pr.parserData["mc"].bot
        bot.DebugMode=not bot.DebugMode
        return ["Debug:"+ModeText[bot.DebugMode]]

    @Events.onCmd("status")
    @AdminOnly
    async def status(pr:ParseResult):
        bot:Bot=pr.parserData["mc"].bot
        return [await bot.GetStatus(pr.command)] # status / version

    # @Events.onCmd("restart")
    # @AdminOnly
    # def restart(pr:ParseResult):
    #     bot:Bot=pr.parserData["mc"].bot
    #     time=pr.getToType("time",3000,int)
    #     time=max(1,time)
    #     if time<300: # 太小的话看作是秒
    #         time*=1000
    #     bot.Restart(time)
    #     return [f"约 {time/1000}s 后重启插件~"]

    @Events.onCmd("reload")
    @AdminOnly
    async def reload(pr:ParseResult):
        bot:Bot=pr.parserData["mc"].bot
        msg:Message=pr.raw
        ps=pr.paramStr.strip()
        rt="all"
        if ps:
            rt=ps
        results=await bot.Reload(rt)
        msgc=msg.copy(srcAsDst=True)
        if results:
            msgc.content=f"已重载：{'、'.join(results)}"
        else:
            msgc.content="什么都没有重载！？"
        await bot.Send(msgc)
        return []

    Command("-cq")
    @Events.onCmd("cq")
    def cqcode(pr:ParseResult):
        content=CQunescapeComma(pr.paramStr)
        # print(content)
        return [Content(content)]

    Command("-ban").names("绝交","不理").opt(["-qq","--qq","-q","--q"],OPT.M,"qq号").opt(["-group","--group","-g","--g"],OPT.M,"群号").opt(["--preset","-preset","-p","--p"],OPT.M,"预设发送集合")
    Command("-unban").names("和好","理").opt(["-qq","--qq","-q","--q"],OPT.M,"qq号").opt(["-group","--group","-g","--g"],OPT.M,"群号").opt(["--preset","-preset","-p","--p"],OPT.M,"预设发送集合")

    @Events.onCmd("ban")
    @Events.onCmd("unban")
    async def ban(pr:ParseResult):
        msg:Message=pr.raw
        bot:Bot=msg.selector.bot
        isBan=pr._cmd.name=="ban"
        action="绝交" if isBan else "和好"
        # content=None
        # if pr.params:
        #     content=pr.paramStr
        #     if content.strip()=="update":
        #         content=bot.update
        qqs={}
        qqs=fillQQs(pr["qq"],qqs,MessageType.Private)
        qqs=fillQQs(pr["group"],qqs,MessageType.Group)
        presetName=pr["preset"]
        if presetName:
            if isinstance(presetName,str):
                presetName=[presetName]
            for psn in presetName:
                ps=broadcastPreset.get(psn)
                if ps:
                    qqs=fillQQs(ps,qqs)
        if qqs:
            # if content:
            #     await bot.AsyncBroadcast(qqs,Message.build(content))
            num=0
            result=""
            for k,v in qqs.items():
                strQQ=[ str(qq) for qq in v ]
                if k==MessageType.Private:
                    if isBan:
                        bot.BanQQ.update(strQQ)
                    else:
                        bot.BanQQ.difference_update(strQQ)
                elif k==MessageType.Group:
                    if isBan:
                        bot.BanGroup.update(strQQ)
                    else:
                        bot.BanGroup.difference_update(strQQ)
                result+=f"{k}: {', '.join(strQQ)}\n"
                num+=len(v)
            result+=f"和 {num} 个人{action}了"
            # print(bot.BanQQ)
            # print(bot.BanGroup)
            return [result]
        return ["我不知道要和谁{action}"]


@Events.on(RequestSelector.getEventName()) # 这种事件需要在默认的 CommandCore 上
async def request(req:Request,bot:Bot):
    if bot.AdminQQ: # 把请求信息推给管理员
        qqs=filter(lambda qq: not bot.IsMe(qq),bot.AdminQQ)
        # qqs=[ qq for qq in self.bot.AdminQQ if not self.bot.IsMe(qq) ]
        msg=Message.build(str(req),dst=0,mtype=MessageType.Private)
        # bot.AddBackTask(bot.AsyncBroadcast,qqs,msg)
        asyncio.create_task(bot.Broadcast(qqs,msg))

@Events.on(EventNames.Startup)
def botStartup(bot:Bot):
    global AdminMode
    AdminMode=getattr(bot,"AdminMode",False)
    loadBroadcastPreset(bot)

@Events.on(EventNames.Shutdown)
def botShutdown(bot:Bot):
    if AdminMode:
        setattr(bot,"AdminMode",AdminMode)

# @Events.on(EventNames.MsgCoreInit)
# def coreInit(core:MCore):
#     loadBroadcastPreset(core.bot)
