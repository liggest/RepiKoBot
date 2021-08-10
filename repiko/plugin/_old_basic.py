from repiko.msg.message import Message

import repiko.module.ygoOurocg_ver4 as ygotest
from repiko.module.calculator import Calculator
from repiko.module.ygoServerRequest import ygoServerRequester
# from repiko.module.helper import Helper
from repiko.module.google_translatation import gTranslator
from repiko.module.ygo.card import Card
from repiko.module.hitokoto import HitokotoRequester
from repiko.module.str2image import str2greyPng
import random
import datetime
import os

from LSparser import *
from LSparser.command import CommandHelper

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
def hello(_):
    return ["喵哈喽~"]

# @Events.onCmd("help")
# def helpinfo(pr:ParseResult):
#     h=Helper("./help")
#     page=pr.getByType("p","1")
#     if page.isdigit():
#         page=int(page)
#     else:
#         page=1
#     if len(pr.params)>0 and pr.parser.core.isMatchPrefix(pr.params[0]):
#         pr.params[0]=pr.params[0][1:]
#     try:
#         return h.getHelp(pr.params,page)
#     except:
#         return ["没找到相关帮助……"]@Events.onCmd("help")
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
    # if cp and not pr.isDefinedCommand():
    if not pr.isDefinedCommand():
        pr=pr.opt("-act",1).parse()
        # pr=cp.parse(pr)
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
def ygocard(pr:ParseResult):
    a=ygotest.ourocg()
    if len(pr.params)==0:
        if pr.getByType("wiki",False,bool):
            return [f"拿去吧~\n{a.wikiLink}"]
        return ["空气怎么查啊！"]
    ver=pr.args.get("ver",False)
    if ver:
        a.SetTranslateEdition(ver)
    rcard=a.FindCardByName( pr.paramStr )
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

@Events.onCmd("ygoserver")
def ygoserver(pr:ParseResult):
    a=ygoServerRequester()
    expression=pr.paramStr
    if not expression.startswith(":"):
        expression=":"+expression
    return [a.request(expression)]

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

@Events.onCmd("luck")
def luck(pr:ParseResult):
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
        return [result]+ygocard(pr)

    return [result]

@Events.onCmd("ygodraw")
def ygodraw(pr:ParseResult):
    cdb=pr.parserData["mc"].data["ygocdb"]
    conf=pr.parserData["mc"].data["ygoconf"]
    cdb.connect()
    cid=cdb.getRandomIDs()[0]
    ct=cdb.getCardByID(cid)
    cdb.close()
    c=Card()
    c.fromCDBTuple(ct,conf.setdict,conf.lfdict)
    resultText=str(c)
    if pr.args.get("im",False):
        filename=str2greyPng(resultText,c.name)
        return [f"[CQ:image,file={filename}]"]
    else:
        return [resultText]

@Events.onCmd("aword")
def aword(pr:ParseResult):
    a=HitokotoRequester()
    if pr is None:
        word=a.request()
        return word
    otypes=pr.args.get("t",[])
    if isinstance(otypes,str):
        otypes=[otypes]
    ctypes=[]
    ctypes+=pr.params
    ctypes+=otypes
    word=a.request(*ctypes)
    return [word]


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
