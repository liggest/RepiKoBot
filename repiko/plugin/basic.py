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

@Events.onCmd("hello")
def hello(_):
    return ["喵哈喽~"]

@Events.onCmd("help")
def helpinfo(pr:ParseResult):
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
    if hasattr(msg,"json") and msg.mtype=="private":
        name=None
        sender=msg.json.get("sender")
        if sender:
            name=sender.get("nickname")
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

@Events.on(EventNames.StartUp)
def botStartUP(bot:Bot):
    copyYGO(bot)

@Events.on(EventNames.MsgCoreInit)
def coreInit(core:MCore):
    initYGO(core)
    initEat(core)
    initLuck(core)
