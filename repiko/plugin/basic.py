import repiko.module.ygoOurocg_ver4 as ygotest
from repiko.module.calculator import Calculator
from repiko.module.ygoServerRequest import ygoServerRequester
from repiko.module.helper import Helper
from repiko.module.google_translatation import gTranslator
from repiko.module.ygo.card import Card
from repiko.module.hitokoto import HitokotoRequester
from repiko.module.str2image import str2greyPng
import random
import datetime

from LSparser import *
from LSparser.command import CommandCore

Command("-hello")
Command("help").names("?","？").opt("-p",1,"页数")
Command("calculate").names("cal").opt("-show",0,"显示计算过程")
Command("roll").names("r").opt("-act",1,"要投骰子的行动")
Command("ygocard").names("yc","ygo").opt("-ver",1,"翻译版本").opt("-wiki",0,"提供wiki链接").opt("-im",0,"以图片发送")
Command("ygoserver").names("ys")
Command("translate").names("ts").opt("-from",1,"源语言").opt("-to",1,"目标语言").opt("-p",0,"显示发音")\
    .opt("-d",0,"检测语言").opt("-donly",0,"只检测语言")
Command("luck").names("jrrp").opt("-yci",0,"根据运值卡查，发送图片")
Command("ygodraw").names("yd","抽卡").opt("-im",0,"以图片发送")
Command("aword").names("aw","一句话","一言").opt(["-t","--t"],1,"句子类型")

Command("eat").names("canteen").opt("-r",0,"重置列表").opt("--l",1,"添加自定义列表").opt("--ban",1,"添加排除列表")
Command("cat").names("猫")

@Events.onCmd("hello")
def hello(cp):
    return ["喵哈喽~"]

@Events.onCmd("help")
def helpinfo(cp):
    h=Helper("./help")
    page=cp.getByType("p","1")
    if page.isdigit():
        page=int(page)
    else:
        page=1
    if len(cp.command["params"])>0 and CommandCore.getLast().isMatchPrefix(cp.command["params"][0]):
        cp.command["params"][0]=cp.command["params"][0][1:]
    try:
        return h.getHelp(cp.command["params"],page)
    except:
        return ["没找到相关帮助……"]

@Events.onCmd("calculate")
def calculate(cp):
    a=Calculator()
    if len(cp.command["params"])==0:
        return ["零最大，所以是∞"]
    expression=cp.getParams()
    r=a.cal([expression,expression+"\n"])
    if r[0]=="error":
        return ["解题过程中卡住了……"]
    elif cp.getByType("show",False,bool):
        return [r[1][:-1]]
    else:
        return [r[0]]

@Events.onCmd("roll")
def rolldice(cp):
    if not cp.isDefinedCommand():
        cp.opt("-act",1).parse()
    a=Calculator()
    cmd=cp["command"]
    act=cp.getByType("act","")
    expression=""
    for params in cp["params"]:
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

@Events.onCmd("ygocard")
def ygocard(cp):
    a=ygotest.ourocg()
    if len(cp.command["params"])==0:
        return ["空气怎么查啊！"]
    if cp.command.get("ver",False):
        a.SetTranslateEdition(cp.command["ver"])
    rcard=a.FindCardByName( cp.getParams() )
    if rcard:
        resultText=str(rcard)
        if cp.command.get("im",False):
            filename=str2greyPng(resultText,rcard.name)
            result=[f"[CQ:image,file={filename}]"]
        else:
            result=[resultText]
    else:
        return ["找不到卡片的说……"]
    if cp.getByType("wiki",False,bool):
        wikilink=a.getWikiLink(rcard)
        if wikilink:
            result.append(wikilink)
        else:
            result.append("并没有找到wiki链接……")
    return result

@Events.onCmd("ygoserver")
def ygoserver(cp):
    a=ygoServerRequester()
    expression=cp.getParams()
    if not expression.startswith(":"):
        expression=":"+expression
    return [a.request(expression)]

@Events.onCmd("translate")
def translate(cp):
    if len(cp.command["params"])==0:
        return ["给点东西让我翻译嘛"]
    text=cp.getParams()
    a=gTranslator()
    donly=cp.getByType("donly",False,bool)
    if donly:
        return a.detectonly(text)
    fromlan=cp.getByType("from","auto")
    tolan=cp.getByType("to","cn")
    poun=cp.getByType("p",False,bool)
    dtct=cp.getByType("d",False,bool)
    return a.trans(text,fromlan=fromlan,tolan=tolan,poun=poun,detect=dtct or donly)

@Events.onCmd("luck")
def luck(cp):
    luckbar=cp.mc.data["luckbar"]
    today=str(datetime.date.today())
    qq=str(cp.sendqq[-1])
    random.seed( today+"-"+qq ) #20xx-xx-xx-xxxxxxxxxx
    luck=random.randint(0,100) #实际上有101种可能
    random.seed()
    result=f"[CQ:at,qq={qq}]的今日运势为 {luck} \n"
    barbody=luck//4
    result+=luckbar[4]*barbody
    barhead=luck%4
    result+=luckbar[barhead]
    if cp.command.get("yci",False):
        cp.command["params"]=[f"No.{luck}"]
        cp.command["im"]=True
        return [result]+ygocard(cp)

    return [result]

@Events.onCmd("ygodraw")
def ygodraw(cp):
    cdb=cp.mc.data["ygocdb"]
    conf=cp.mc.data["ygoconf"]
    cdb.connect()
    cid=cdb.getRandomIDs()[0]
    ct=cdb.getCardByID(cid)
    cdb.close()
    c=Card()
    c.fromCDBTuple(ct,conf.setdict,conf.lfdict)
    resultText=str(c)
    if cp.command.get("im",False):
        filename=str2greyPng(resultText,c.name)
        return [f"[CQ:image,file={filename}]"]
    else:
        return [resultText]

@Events.onCmd("aword")
def aword(cp):
    a=HitokotoRequester()
    if cp is None:
        word=a.request()
        return word
    otypes=cp.command.get("t",[])
    if isinstance(otypes,str):
        otypes=[otypes]
    ctypes=[]
    ctypes+=cp["params"]
    ctypes+=otypes
    word=a.request(*ctypes)
    return [word]


@Events.onCmd("eat")
def where2eat(cp):
    canteen_meta=cp.mc.data["canteen_meta"]
    canteen_current=cp.mc.data["canteen_current"]
    newlist=cp.command.get("l",[])
    if isinstance(newlist,list) and len(newlist)!=0:
        cp.mc.data["canteen_current"]=newlist
        canteen_current=cp.mc.data["canteen_current"]
    banlist=cp.command.get("ban",[])
    if isinstance(banlist,list) and len(banlist)!=0:
        for s in banlist:
            if s in canteen_current:
                canteen_current.remove(s)
    l=len(canteen_current)
    if cp.command.get("r",False) or l==0:
        cp.mc.data["canteen_current"]=canteen_meta.copy()
        canteen_current=cp.mc.data["canteen_current"]
    l=len(canteen_current)
    return[canteen_current.pop(random.randint(0,l-1))]

@Events.onCmd("cat")
def catImage(cp):
    return [r"[CQ:image,file=https://thiscatdoesnotexist.com,cache=0]"]
