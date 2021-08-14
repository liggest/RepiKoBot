from math import nan
from repiko.core.bot import Bot
from repiko.core.constant import EventNames
from repiko.msg.core import MCore
from repiko.msg.message import Message

import repiko.module.ygoOurocg_ver4 as ygotest
from repiko.module.calculator import Calculator
# from repiko.module.ygoServerRequest import ygoServerRequester
# from repiko.module.helper import Helper
from repiko.module.google_translatation import gTranslator
from repiko.module.ygo.card import Card
from repiko.module.ygo.dataloader import cdbReader,confReader
from repiko.module.hitokoto import HitokotoRequester
from repiko.module.str2image import str2greyPng

import random
import datetime
import os
import yaml

from LSparser import *
from LSparser.command import CommandHelper

Command("-hello")
Command("help").names("?","？").opt("-p",OPT.M,"页数")
Command("calculate").names("cal").opt("-show",OPT.N,"显示计算过程")
Command("roll").names("r").opt("-act",OPT.M,"要投骰子的行动")
Command("ygocard").names("yc","ygo").opt("-ver",OPT.M,"翻译版本").opt("-wiki",OPT.N,"提供wiki链接").opt("-im",OPT.N,"以图片发送")
# Command("ygoserver").names("ys")
Command("translate").names("ts").opt("-from",OPT.M,"源语言").opt("-to",OPT.M,"目标语言").opt("-p",OPT.N,"显示发音")\
    .opt("-d",OPT.N,"检测语言").opt("-donly",OPT.N,"只检测语言")
Command("luck").names("jrrp").opt("-yci",OPT.N,"根据运值卡查，发送图片")
Command("ygodraw").names("yd","抽卡").opt("-n",OPT.M,"抽卡数").opt("-im",OPT.N,"以图片发送")
Command("logodraw").names("群赛抽卡","决斗都市","yddc","duelcity").opt("-im",OPT.N,"以图片发送")
Command("aword").names("aw","一句话","一言").opt(["-t","--t"],OPT.M,"句子类型")

Command("eat").names("canteen").opt("-r",OPT.N,"重置列表").opt("--l",OPT.M,"添加自定义列表").opt("--ban",OPT.M,"添加排除列表")
Command("cat").names("猫")

c=Command("duel").names("决斗","duel!","duel！","决斗！","打牌","打牌！","牌","牌！")
c.opt(["-match","-m","-M","-比赛","-三局"],OPT.N,"比赛模式").opt(["-tag","-t","-T","-双打","-麻将"],OPT.N,"双打")
c.opt(["-ot","-OT","-ot混","-OT混"],OPT.N,"OT混").opt(["-tcg","-TCG"],OPT.N,"TCG")
c.opt(["-lp","-LP","-基本分","-生命","-生命值","-血"],OPT.T,"基本分")
c.opt(["-time","-tm","-TM","-时间"],OPT.T,"回合时间")
c.opt(["-tm0","-TM0"],OPT.N,"-tm 0 的简写")
c.opt(["-start","-st","-ST","-起手"],OPT.T,"起手手牌数")
c.opt(["-draw","-dr","-DR","-抽","-抽卡","-抽牌"],OPT.T,"回合抽牌数")
c.opt(["-lflist","-lf","-LF","-禁卡表"],OPT.T,"禁限卡表")
c.opt(["-nolflist","-nf","-NF","-nolf","-NOLF","-无禁卡表","-无禁卡","-无禁限","-无限制"],OPT.N,"无禁限卡表")
c.opt(["-nounique","-nu","-NU","-无独有"],OPT.N,"无独有卡")
c.opt(["-nocheck","-nc","-NC","-不检查","-不检查卡组"],OPT.N,"不检查卡组")
c.opt(["-noshuffle","-ns","-NS","-不洗牌"],OPT.N,"不洗牌")
c.opt(["-ai","-AI","-人机"],OPT.N,"人机")
c.opt(["-rule","-mr","-MR","-规则"],OPT.T,"大师规则")
c.opt(["-server","-s","-服","-服务器"],OPT.M,"服务器")
c.opt(["-233"],OPT.N,"233服-233").opt(["-2333"],OPT.N,"233服-2333").opt(["-23333"],OPT.N,"233服-23333")
c.opt(["-me","-ME","-mine","-我","-俺","-老子"],OPT.N,"我的房")
c.opt(["-set","-盖放"],OPT.T,"记录房").opt(["-get","-发动","-检索","-召唤","-特招"],OPT.M,"得到房")
c.opt(["-del","-remove","-破坏","-除外","-送去墓地"],OPT.T,"移除房")
c.opt(["-random","-r","-ran"],OPT.N,"随机房间名")

@Events.onCmd("hello")
def hello(_):
    return ["喵哈喽~"]

@Events.onCmd("help")
def helpinfo(pr:ParseResult):
    if f"{pr.type}{pr.command}" in ("!?","！？"):
        return [] # !? 和 ！？ 不触发

    root="./help"
    core=pr.parser.core
    if core.name!=CommandCore.default:
        root=os.path.join(root,core.name)
    h=CommandHelper(root,core)
    page=pr.getToType("p",1,int)
    result=h.getHelp(pr.params,page)
    if result:
        return [result]
    return ["是没见过的帮助呢"]

@Events.onCmd("calculate")
def calculate(pr:ParseResult):
    a=Calculator()
    if len(pr.params)==0:
        return ["零最大，所以是∞"]
    expression=pr.paramStr
    r=a.cal([expression,expression+"\n"])
    if r[0]=="error":
        return ["解题过程中卡住了……"]
    elif pr.getByType("show",False,bool):
        return [r[1][:-1]]
    else:
        return [r[0]]

@Events.onCmd("roll")
def rolldice(pr:ParseResult):
    if not pr.isDefinedCommand():
        pr=pr.opt("-act",1).parse()
    a=Calculator()
    cmd=pr.command
    act=pr.getByType("act","")
    expression=""
    for params in pr.params:
        if params.isalpha() and not "d" in params:
            act+=" "+params
        else:
            expression+=params
    expression=expression.strip().lower()
    act=act.strip()
    if cmd.startswith("rolld") or cmd.startswith("rd"):
        dindex=cmd.find("d")
        return [a.dicetext(cmd[dindex:]+expression,act)]
    if expression=="":
        return [a.dicetext("1d100",act)]
    else:
        return [a.dicetext(expression,act)]

@Events.onUndefinedCmd
def undefined(pr:ParseResult, cp:CommandParser):
    cmd=pr.command
    if cmd.startswith("rolld") or cmd.startswith("rd"):
        pr.output.append(rolldice(pr))

@Events.onCmd("ygocard")
async def ygocard(pr:ParseResult):
    a=ygotest.ourocg()
    if len(pr.params)==0:
        if pr.getByType("wiki",False,bool):
            return [f"拿去吧~\n{a.wikiLink}"]
        return ["空气怎么查啊！"]
    ver=pr.args.get("ver",False)
    if ver:
        a.SetTranslateEdition(ver)
    rcard=await a.AsyncSearchByName( pr.paramStr )
    if rcard:
        resultText=str(rcard)
        if pr.args.get("im",False):
            filename=str2greyPng(resultText,rcard.name)
            result=[f"[CQ:image,file={filename}]"]
        else:
            result=[resultText]
    else:
        return ["找不到卡片的说……"]
    if pr.getByType("wiki",False,bool):
        wikilink=a.getWikiLink(rcard)
        if wikilink:
            result.append(wikilink)
        else:
            result.append("并没有找到wiki链接……")
    return result

# @Events.onCmd("ygoserver")
# def ygoserver(pr:ParseResult):
#     a=ygoServerRequester()
#     expression=pr.paramStr
#     if not expression.startswith(":"):
#         expression=":"+expression
#     return [a.request(expression)]

@Events.onCmd("translate")
def translate(pr:ParseResult):
    if len(pr.params)==0:
        return ["给点东西让我翻译嘛"]
    text=pr.paramStr
    a=gTranslator()
    donly=pr.getByType("donly",False,bool)
    if donly:
        return a.detectonly(text)
    fromlan=pr.getByType("from","auto")
    tolan=pr.getByType("to","cn")
    poun=pr.getByType("p",False,bool)
    dtct=pr.getByType("d",False,bool)
    return a.trans(text,fromlan=fromlan,tolan=tolan,poun=poun,detect=dtct or donly)

def initLuck(core:MCore):
    core.data["luckbar"]=["","一","二","三","亖"]

@Events.onCmd("luck")
async def luck(pr:ParseResult):
    luckbar=pr.parserData["mc"].data["luckbar"]
    today=str(datetime.date.today())
    msg:Message=pr.raw
    qq=str(msg.realSrc)
    random.seed( today+"-"+qq ) #20xx-xx-xx-xxxxxxxxxx
    luck=random.randint(0,100) #实际上有101种可能
    random.seed()
    name=f"[CQ:at,qq={qq}]"
    if msg.mtype=="private":
        name=msg.getSrcName()
    if name:
        result=f"{name}的今日运势为 {luck} \n"
    else:
        result=f"今日运势为 {luck} \n"
    barbody=luck//4
    result+=luckbar[4]*barbody
    barhead=luck%4
    result+=luckbar[barhead]
    if pr.args.get("yci",False):
        pr.params=[f"No.{luck}"]
        pr.args["im"]=True
        return [result]+await ygocard(pr)
    return [result]

ygodir="./ygo/"

def copyYGO(bot:Bot):
    import shutil
    cplist=["cards.cdb","lflist.conf","strings.conf"]
    # if not self.config.has_option("ygo","ygopath"):
    if not (bot.config.get("ygo") and bot.config["ygo"].get("ygoPath")):
        return
    ygopath=bot.config["ygo"]["ygoPath"]
    if not os.path.exists(ygodir):
        os.mkdir(ygodir)
    for f in cplist:
        fpath=os.path.join(ygopath,f)
        if os.path.exists(fpath):
            shutil.copy(fpath,ygodir)
            print(f"拷贝{fpath}到{ygodir}")
        else:
            print(f"没有发现{fpath}")

def initYGO(core:MCore):
    ygopath=ygodir
    core.data["ygocdb"]=cdbReader(path=ygopath+"cards.cdb")
    conf=confReader()
    conf.loadLFlist(ygopath+"lflist.conf")
    conf.loadSets(ygopath+"strings.conf")
    core.data["ygoconf"]=conf

@Events.onCmd("ygodraw")
def ygodraw(pr:ParseResult):
    num=pr.getToType("n",0,int)
    if pr.paramStr.isdigit():
        num+=int(pr.paramStr)
    cdb:cdbReader=pr.parserData["mc"].data["ygocdb"]
    conf:confReader=pr.parserData["mc"].data["ygoconf"]
    result=[]
    with cdb:
        if num<=1:
            cid=cdb.getRandomIDs()[0]
            ct=cdb.getCardByID(cid)
            c=Card()
            c.fromCDBTuple(ct,conf.setdict,conf.lfdict)
            name=c.name
            resultText=str(c)
        else:
            if num>60:
                num=60
                result.append("一次出太多会刷屏\n先丢你一个卡组的份哦…")
            ct=cdb.getRandomNames(count=num)
            name=ct[0]
            resultText="\n".join(ct)
    if pr.args.get("im",False):
        filename=str2greyPng(resultText,name)
        result.append(f"[CQ:image,file={filename}]")
    else:
        result.append(resultText)
    return result

@Events.onCmd("logodraw")
def logodraw(pr:ParseResult):
    pr.command="yd"
    pr.args["n"]=20
    return ygodraw(pr)

@Events.onCmd("aword")
async def aword(pr:ParseResult):
    a=HitokotoRequester()
    if pr is None:
        word=await a.aRequest()
        return word
    otypes=pr.args.get("t",[])
    if isinstance(otypes,str):
        otypes=[otypes]
    ctypes=[]
    ctypes+=pr.params
    ctypes+=otypes
    word=await a.aRequest(*ctypes)
    return [word]

def initEat(core:MCore):
    core.data["canteen_meta"]=["新1","新2","新3","新4","老1","老2","楼上楼","清真餐厅","风味餐厅","小南门","大南门","西北风"]
    core.data["canteen_current"]=core.data["canteen_meta"].copy()

@Events.onCmd("eat")
def where2eat(pr:ParseResult):
    canteen_meta=pr.parserData["mc"].data["canteen_meta"]
    canteen_current=pr.parserData["mc"].data["canteen_current"]
    newlist=pr.args.get("l",[])
    if isinstance(newlist,list) and len(newlist)!=0:
        pr.parserData["mc"].data["canteen_current"]=newlist
        canteen_current=pr.parserData["mc"].data["canteen_current"]
    banlist=pr.args.get("ban",[])
    if isinstance(banlist,list) and len(banlist)!=0:
        for s in banlist:
            if s in canteen_current:
                canteen_current.remove(s)
    l=len(canteen_current)
    if pr.args.get("r",False) or l==0:
        pr.parserData["mc"].data["canteen_current"]=canteen_meta.copy()
        canteen_current=pr.parserData["mc"].data["canteen_current"]
    l=len(canteen_current)
    return[canteen_current.pop(random.randint(0,l-1))]

@Events.onCmd("cat")
def catImage(_):
    return [r"[CQ:image,file=https://thiscatdoesnotexist.com,cache=0]"]

boolCodeMap={"match":"M","tag":"T","tcg":"TO","ot":"OT","nolflist":"NF","nounique":"NU","nocheck":"NC","noshuffle":"NS","ai":"AI"}
intCodeMap={"lp":"LP","time":"TM","start":"ST","draw":"DR","lflist":"LF","rule":"MR"}
intRangeMap={"lp":(1,99999,8000),"time":(0,999,3),"start":(1,40,5),"draw":(0,35,1),"lflist":(1,99999,1),"rule":(1,5,5)} 
# (下限，上限，默认值) 禁卡表数量一直在变化，故不设上限

roomFile="MemberRoom.yaml"
memberRooms={} # {"room":"","server":""}
servers={}

def initDuel(core:MCore):
    global memberRooms,servers
    roomFilePath=os.path.join(ygodir,roomFile)
    if os.path.exists(roomFilePath):
        with open(roomFilePath,encoding="utf-8") as f:
            memberRooms=yaml.safe_load(f)
    bot:Bot=core.bot
    servers=bot.config.get("ygo",{}).get("servers",{})

def saveDuel():
    if not memberRooms:
        return
    roomFilePath=os.path.join(ygodir,roomFile)
    with open(roomFilePath,"w",encoding="utf-8") as f:
        yaml.safe_dump(memberRooms,f,encoding="utf-8",allow_unicode=True)
    
def randomRoomName(pr:ParseResult):
    cdb:cdbReader=pr.parserData["mc"].data["ygocdb"]
    conf:confReader=pr.parserData["mc"].data["ygoconf"]
    result=[]
    with cdb:
        ct=cdb.getRandomNames(count=random.randint(2,6))
        result=[n[0] for n in ct]
    return "".join(result)

@Events.onCmd("duel")
def duel(pr:ParseResult):
    msg:Message=pr.raw
    result=[]
    room=pr.paramStr.strip()
    prefix=set()
    roomInfo:dict=None
    srv=None
    if not pr["random"]:
        if not pr.params:
            pr.args["me"]=True
        key=pr["get"]
        if key:
            roomInfo=memberRooms.get(key)
        elif pr["me"]:
            roomInfo=memberRooms.get(msg.realSrc)
        if roomInfo:
            fullRoom:str=roomInfo["room"]
            roomList=fullRoom.split("#")
            if len(roomList)<2:
                room=fullRoom
            else:
                prefix.update(roomList[0].split(","))
                room="#".join(roomList[1:])
            srv:str=roomInfo.get("server")
    if not room or pr["random"]:
        room=randomRoomName(pr)
    if pr.getByType("time",None,bool) or pr["tm0"]: # -tm -> -tm 0 
        pr.args["time"]="0"
    for arg in pr.args:
        code=boolCodeMap.get(arg)
        if code:
            prefix.add(code)
        else:
            code=intCodeMap.get(arg)
            if code and not isinstance(pr[arg],bool):
                minVal,maxVal,defaultVal=intRangeMap[arg]
                val=pr.getToType(arg,None,int)
                if val is not None:
                    val=max(minVal,val)
                    val=min(maxVal,val)
                    prefix.add(f"{code}{val}")
    if prefix:
        fullRoom=f"{','.join(prefix)}#{room}"
    else:
        fullRoom=room
    result.append(fullRoom)
    if not pr["server"]:
        for s in ("23333","233","2333"):
            if pr[s]:
                pr.args["server"]=s
    if not srv or pr["server"]:
        srv=pr.getByType("server","2333")
    noserver=(None,None)
    if srv.startswith("233"):
        host,port=servers.get("233",noserver)
        port=int(f"2{'3'*srv.count('3')}")
    elif srv.endswith("编年史"):
        host,port=servers.get("编年史",noserver)
    elif srv=="2pick" or srv=="轮抽":
        host,port=servers.get("2pick",noserver)
    elif srv.startswith("复读") or srv.lower()=="repiko":
        host,port=servers.get("repiko",noserver)
    else:
        host,port=noserver
    if host and port:
        result.append(f"{host}  {port}")
    if pr["set"]:
        setKey=pr.getByType("set",msg.realSrc) #无值的场合使用QQ号
        srcName=msg.getSrcName()
        if fullRoom:
            roomInfo={"room":fullRoom}
            if host and port:
                roomInfo["server"]=srv
            if srcName:
                roomInfo["name"]=srcName
            memberRooms[setKey]=roomInfo
            if isinstance(setKey,str):
                result.append(f"记录房间为 {setKey}")
            else:
                name=f"[CQ:at,qq={setKey}]"
                if msg.mtype=="private" and srcName:
                    result.append(f"记录了{srcName}的房间")
                else:
                    result.append(f"记录了房间")
    if pr["del"]:
        delKey=pr.getByType("del",msg.realSrc)
        if delKey in memberRooms:
            memberRooms.pop(delKey)
            if isinstance(delKey,str):
                result.append(f"移除了房间 {delKey}")
            else:
                name=f"[CQ:at,qq={delKey}]"
                if msg.mtype=="private":
                    name=msg.getSrcName()
                if name:
                    result.append(f"移除了{name}的房间")
                else:
                    result.append(f"移除了房间")
    return result

@Events.on(EventNames.StartUp)
def botStartUP(bot:Bot):
    copyYGO(bot)

@Events.on(EventNames.MsgCoreInit)
def coreInit(core:MCore):
    initYGO(core)
    initDuel(core)
    initEat(core)
    initLuck(core)

@Events.on(EventNames.ShutDown)
def botShutDown(bot:Bot):
    saveDuel()

# c.showHelp=True
# print(c.getHelp())