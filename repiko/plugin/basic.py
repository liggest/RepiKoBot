
from repiko.core.bot import Bot
from repiko.core.constant import EventNames, MessageType
from repiko.core.log import logger
from repiko.core.config import Config, Pattern, pluginConfig, PluginUnits
from repiko.msg.content import Content
from repiko.msg.core import MCore
# from repiko.msg.message import Message
from repiko.msg.data import Message
# from repiko.msg.part import MessagePart,Share,Image,At,Text
from repiko.msg.part import MessagePart,Image,At,Text
from repiko.msg.util import CQunescapeComma,CQunescape

import repiko.module.ygoOurocg_ver4 as ygotest
from repiko.module.ygoBG import BaiGe
from repiko.module.ygoRoom import YGORoom
from repiko.module.calculator import Calculator
# from repiko.module.ygoServerRequest import ygoServerRequester
# from repiko.module.helper import Helper
from repiko.module.ygo.card import Card
from repiko.module.ygo.dataloader import cdbReader,confReader,ShrinkLevel
from repiko.module.ygo.sqlbuilder import SQLBuilder
from repiko.module.hitokoto import HitokotoRequester
from repiko.module.str2image import str2greyPng,getFilePath as getImgPath,initFont as initNormalFont
from repiko.module.util import redirect,asyncRedirect,CONS,Share

from repiko.module import 麻将
from repiko.module.AA import AAMZ
from repiko.module.AA.image import AA2img,initFont as initAAFont
from repiko.module.tex import initFont as initTexFont,atext2img,LatexError

import random
import datetime
import os
import re
from typing import Annotated
# from pathlib import Path
# import yaml

from LSparser import *
from LSparser.command import CommandHelper

Command("-hello")
Command("help").names("?","？").opt("-p",OPT.M,"页数")# .opt("-im",OPT.N,"以图片发送")
Command("calculate").names("cal").opt("-show",OPT.N,"显示计算过程")
Command("roll").names("r").opt("-act",OPT.M,"要投骰子的行动")
(Command("ygocard").names("yc","bg","卡查","查卡").opt("-im",OPT.N,"以图片发送").opt(["-pic","-p"],OPT.N,"卡图")
    .opt("-database",OPT.N,"数据库链接").opt("-QA",OPT.N,"Q&A链接").opt("-wiki",OPT.N,"wiki链接")
    .opt("-yugipedia",OPT.N,"Yugipedia链接").opt("-ourocg",OPT.N,"OurOcg链接")
    .opt(["-script","-lua"],OPT.N,"脚本链接").opt(["-ocgRule","-rule"],OPT.N,"裁定链接").opt(["-url","-link"],OPT.N,"百鸽链接")
    #.opt("-ygorg",OPT.N,"YGOrg链接")
    .opt("-reload",OPT.N,"重载图片")
)
Command("ycpic").names("ycp","bgpic","bgp")

Command("ygoocg").names("yo","ourocg").opt("-ver",OPT.M,"翻译版本").opt("-wiki",OPT.N,"提供wiki链接").opt("-im",OPT.N,"以图片发送").opt(["-pic","-p"],OPT.N,"卡图").opt("-reload",OPT.N,"重载图片")
# Command("ygoserver").names("ys")
Command("luck").names("jrrp").opt("-yc",OPT.N,"根据运值卡查").opt("-yci",OPT.N,"根据运值卡查，发送图片").opt("-ycp",OPT.N,"根据运值卡查，发送卡图")
(Command("ygodraw").names("yd").opt("-n",OPT.M,"抽卡数").opt("-im",OPT.N,"以图片发送").opt(["-pic","-p"],OPT.N,"卡图")
    .opt(["-notoken","-nt","-无衍生物"],OPT.N,"不含衍生物").opt(["-noalias","-na","-无同名卡"],OPT.N,"不含同名卡")
    .opt(["-main","-主卡组"],OPT.N,"只含主卡组").opt(["-extra","-ex","-额外"],OPT.N,"只含额外")
    .opt("-reload",OPT.N,"重载图片")
)
Command("ydpic").names("ydp","抽卡")
Command("logodraw").names("群赛抽卡","决斗都市","yddc","duelcity").opt("-im",OPT.N,"以图片发送")
Command("aword").names("aw","一句话","一言","hitokoto","htkt").opt(["-t","--t"],OPT.M,"句子类型")

Command("eat").names("canteen").opt("-r",OPT.N,"重置列表").opt("--l",OPT.M,"添加自定义列表").opt("--ban",OPT.M,"添加排除列表")
Command("cat").names("猫")

(Command("duel").names("决斗","duel!","duel！","决斗！","打牌","打牌！","牌","牌！","房")
    .opt(["-match","-m","-M","-比赛","-三局"],OPT.N,"比赛模式").opt(["-tag","-t","-T","-双","-双打","-麻将"],OPT.N,"双打")
    .opt(["-ot","-OT","-ot混","-OT混"],OPT.N,"OT混").opt(["-tcg","-TCG"],OPT.N,"TCG")
    .opt(["-lp","-LP","-基本分","-生命","-生命值","-血"],OPT.T,"基本分")
    .opt(["-time","-tm","-TM","-时间","-限时"],OPT.T,"回合时间")
    .opt(["-tm0","-TM0","-不限时"],OPT.N,"-tm 0 的简写")
    .opt(["-start","-st","-ST","-起手"],OPT.T,"起手手牌数")
    .opt(["-draw","-dr","-DR","-抽","-抽卡","-抽牌"],OPT.T,"回合抽牌数")
    .opt(["-lflist","-lf","-LF","-禁卡表"],OPT.T,"禁限卡表")
    .opt(["-nolflist","-nf","-NF","-nolf","-NOLF","-无禁卡表","-无禁卡","-无禁限","-无限制"],OPT.N,"无禁限卡表")
    .opt(["-nounique","-nu","-NU","-无独有"],OPT.N,"无独有卡")
    .opt(["-nocheck","-nc","-NC","-不检查","-不检查卡组"],OPT.N,"不检查卡组")
    .opt(["-noshuffle","-ns","-NS","-不洗牌"],OPT.N,"不洗牌")
    .opt(["-ai","-AI","-人机"],OPT.N,"人机")
    .opt(["-rule","-mr","-MR","-规则"],OPT.T,"大师规则")
    .opt(["-server","-s","-服","-服务器"],OPT.T,"服务器")
    .opt(["-233"],OPT.N,"233服-233").opt(["-2333"],OPT.N,"233服-2333").opt(["-23333"],OPT.N,"233服-23333")
    .opt(["-me","-ME","-mine","-我","-俺","-老子"],OPT.N,"我的房")
    .opt(["-set","-盖放"],OPT.T,"记录房").opt(["-get","-发动","-检索","-召唤","-特招"],OPT.M,"得到房")
    .opt(["-del","-remove","-破坏","-除外","-送去墓地"],OPT.T,"移除房")
    .opt(["-random","-r","-ran"],OPT.N,"随机房间名")
)
Command("duelset").names("setduel","设房","盖牌","盖放牌")
Command("dueldel").names("delduel","删房","炸牌","破坏牌","除外牌","送墓牌")
Command("server").names("srv","服务器","服").opt("-l",OPT.N,"列出所有")

Command("mahjong").names("maj","麻将","麻雀","雀").opt("-n",OPT.M,"张数")#.opt(["-和","-胡"],OPT.N,"和牌")

Command("AA").names("aa").opt(["-R18","-r18"],OPT.N,"嘿嘿许可")

def toLS(*args):
    for x in args:
        yield f"--{x}"
        yield f"-{x}"

(Command("ygocdb").names("ycdb","cdb").opt("-im",OPT.N,"以图片发送")
    .opt([*toLS("race","种族","族")],OPT.M,"种族")
    .opt([*toLS("attr","属性")],OPT.M,"属性")
    .opt([*toLS("type","t","种类","类型")],OPT.M,"卡片类型")
    .opt([*toLS("level","lv","LV","Lv","l","L","等级","星")],OPT.M,"等级")
    .opt([*toLS("rank","r","R","阶级","阶")],OPT.M,"阶级")
    .opt([*toLS("link","LINK","Link","连接","链接")],OPT.M,"连接标识")
    .opt([*toLS("P","刻度","灵摆")],OPT.M,"灵摆刻度")
    .opt([*toLS("atk","ATK","Atk","攻击力","攻击","打点","攻")],OPT.M,"攻击力")
    .opt([*toLS("def","DEF","Def","守备力","防御力","守备","防御","守","防")],OPT.M,"守备力")
    .opt([*toLS("atk+def","a+d","攻守和","攻防和","攻加守","攻加防","攻守","攻防","魂")],OPT.M,"攻守和")
    .opt([*toLS("id","Id","ID","卡号","卡密")],OPT.M,"卡片密码")
    .opt(["-atk=def","-a=d","-攻守相同","-攻守相等","-等攻守","-等攻防","-同攻守","-同攻防","-攻防相同","-攻防相等","-机巧"],OPT.N,"是否攻守相同")
    .opt(["-page","-p"],OPT.M,"页数")
)
@Events.onCmd("hello")
def hello(_):
    return ["喵哈喽~"]

CommandHelper.lineLimit=20

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
        return [CQunescapeComma(result)]
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
        pr=pr.opt("-act",OPT.M).parse()
    a=Calculator()
    cmd=pr.command
    act=pr.getByType("act","")
    expression=""
    symbols={ *Calculator.symbol, *"0123456789.dD" } # 算式用到的字符集合
    for params in pr.params:
        chars=set(params)
        if chars - symbols: # 有不在 symbols 中的字符
        # if params.isalpha() and not "d" in params:
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

linkNames=["url","database","QA","wiki","yugipedia","ourocg","script","ocgRule"] # "ygorg"

@Events.onCmd("ygocard")
async def ygocard(pr:ParseResult):
    a=BaiGe()
    if len(pr.params)==0:
        if pr.getByType("wiki",False,bool):
            return [f"拿去吧~\n{ygotest.ourocg.wikiLink}"]
        return ["空气怎么查啊！"]
    rcard:Card=await a.asyncSearch(pr.paramStr)
    if rcard:
        resultText=str(rcard)
        result=[]
        if pr.getByType("pic",False,bool) and rcard.img:
            result.append(Image(rcard.img) if not pr["reload"] else Image(rcard.img,cache=False)) 
            #f"[CQ:image,file={rcard.img}]"
        elif pr.args.get("im",False):
            filename=str2greyPng(resultText,rcard.name)
            result.append(Image(filename) if not pr["reload"] else Image(filename,cache=False)) 
            # f"[CQ:image,file={filename}]"
        else:
            result.append(resultText)
        for ln in linkNames:
            if pr.getByType(ln,False,bool):
                link=getattr(rcard,ln)
                description=pr._cmd.shortOpts[f"-{ln}"].help
                description=f"{rcard.name}的{description}"
                if link:
                    # result.append(link)
                    result.append(Share(link,title=description,content=link).to(pr))
                else:
                    result.append(f"并没有找到{description}……")
        # if pr.getByType("rule",False,bool) and rcard.ocgRule:
        #     result.append(rcard.ocgRule)
    else:
        return ["找不到卡片的说……"]
    return result

Events.onCmd("ycpic")(asyncRedirect("ygocard",[CONS,"-pic"],ygocard))

@Events.onCmd("ygoocg")
async def ygoocg(pr:ParseResult):
    a=ygotest.ourocg()
    if len(pr.params)==0:
        if pr.getByType("wiki",False,bool):
            return [f"拿去吧~\n{a.wikiLink}"]
        return ["空气怎么查啊！"]
    ver=pr.args.get("ver",False)
    if ver:
        a.SetTranslateEdition(ver)
    rcard:Card=await a.AsyncSearchByName( pr.paramStr )
    if rcard:
        resultText=str(rcard)
        result=[]
        if pr.getByType("pic",False,bool) and rcard.img:
            result.append(Image(rcard.img) if not pr["reload"] else Image(rcard.img,cache=False)) 
        elif pr.args.get("im",False):
            filename=str2greyPng(resultText,rcard.name)
            result.append(Image(filename) if not pr["reload"] else Image(filename,cache=False)) 
        else:
            result.append(resultText)
    else:
        return ["找不到卡片的说……"]
    if pr.getByType("wiki",False,bool):
        wikilink=a.getWikiLink(rcard)
        description=f"{rcard.name}的wiki链接"
        if wikilink:
            # result.append(wikilink)
            result.append(Share(wikilink,title=description,content=wikilink).to(pr))
        else:
            result.append(f"并没有找到{description}……")
    return result

# @Events.onCmd("ygoserver")
# def ygoserver(pr:ParseResult):
#     a=ygoServerRequester()
#     expression=pr.paramStr
#     if not expression.startswith(":"):
#         expression=":"+expression
#     return [a.request(expression)]

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
    if luck==100 and random.randint(1,10)==10:
        luck=1000 # 1000%!!!
    random.seed()
    name=f"[CQ:at,qq={qq}]"
    if msg.mtype=="private":
        name=msg.getSrcName()
    if name:
        result=f"{name}的今日运势为 {luck} \n"
    else:
        result=f"今日运势为 {luck} \n"
    if luck==1000:
        result=f"{result.strip()}！！！ \n"
    barbody=luck//4
    result+=luckbar[4]*barbody
    barhead=luck%4
    result+=luckbar[barhead]
    if pr.args.get("yc") or pr.args.get("yci") or pr.args.get("ycp"):
        pr.params=[f"No.{luck}"]
        if pr.args.get("ycp"):
            pr.args["pic"]=True
        elif pr.args.get("yci"):
            pr.args["im"]=True
        return [result]+await ygocard(pr)
    return [result]

ygodir="./ygo/"

# ServerUnit=Config.Unit("servers",tuple[str,int])
class ServerUnit(Pattern):
    pass

ServerUnit.addDefault("233", ("s1.ygo233.com",233))
ServerUnit.addDefault("编年史", ("duelstart.com",2333))
ServerUnit.addDefault("2pick", ("2pick.mycard.moe",765))

# ygocfg=Config("ygo.toml")

# @Config.considerClass
class YGOConfig(Pattern):
    """  ygo 相关指令的设置  """
    ygoPath:Annotated[str,"ygopro 路径"]
    servers:Annotated[ServerUnit,"服务器列表"]
    # = {
    #     "233": ("s1.ygo233.com",233),
    #     "编年史": ("duelstart.com",2333),
    #     "2pick": ("2pick.mycard.moe",765)
    # }

PluginUnits.addDefault("ygo",annotation=YGOConfig)

@pluginConfig.on
def initYGOplugin(config:dict, bot:Bot):
    data=config.get("ygo")
    copyYGO(data)
    initYGO(bot.mc)
    initDuel(data)

def copyYGO(data:YGOConfig):
    import shutil
    cplist=["cards.cdb","lflist.conf","strings.conf"]
    # if not self.config.has_option("ygo","ygopath"):
    # if "ygo" not in bot.config:
    if not data:
        return logger.error(f"YGO 配置不存在！")
    if not ((ygopath:=data.ygoPath) and os.path.exists(ygopath)):
        return logger.error(f"YGO 路径 {ygopath!r} 不存在！")
    if not os.path.exists(ygodir):
        os.mkdir(ygodir)
    for f in cplist:
        fpath=os.path.join(ygopath,f)
        if os.path.exists(fpath):
            shutil.copy(fpath,ygodir)
            logger.info(f"拷贝 {fpath!r} 到 {ygodir!r}")
        else:
            logger.error(f"没有发现 {fpath!r}")

def initYGO(core:MCore):
    ygopath=ygodir
    if os.path.exists(p:=os.path.join(ygopath,"cards.cdb")):
        core.data["ygocdb"]=cdbReader(path=p)
    conf=confReader()
    if os.path.exists(p:=os.path.join(ygopath,"lflist.conf")):
        conf.loadLFlist(p)
    if os.path.exists(p:=os.path.join(ygopath,"strings.conf")):
        conf.loadSets(p)
    core.data["ygoconf"]=conf

@Events.onCmd("ygodraw")
def ygodraw(pr:ParseResult):
    num=pr.getToType("n",0,int)
    if pr.paramStr.isdigit() and not pr["pic"]: # 最多只出1张图
        num+=int(pr.paramStr)
    levels=[]
    if pr["notoken"]:
        levels.append(ShrinkLevel.NoToken)
    if pr["noalias"]:
        levels.append(ShrinkLevel.NoAlias)
    if pr["main"]:
        levels.append(ShrinkLevel.NoExtra)
    elif pr["extra"]:
        levels.append(ShrinkLevel.NoMain)
    if not levels:
        levels=ShrinkLevel.No
    cdb:cdbReader=pr.parserData["mc"].data["ygocdb"]
    conf:confReader=pr.parserData["mc"].data["ygoconf"]
    result=[]
    with cdb:
        if num<=1:
            cid=cdb.getRandomIDs(shrink=levels)[0]
            ct=cdb.getCardByID(cid)
            c=Card()
            c.fromCDBTuple(ct,conf.setdict,conf.lfdict)
            name=c.name
            if pr.getByType("pic",False,bool):
                result.append(Image(BaiGe.imgLink(c.id)) if not pr["reload"] else Image(BaiGe.imgLink(c.id),cache=False))
            resultText=str(c)
        else:
            if num>60:
                num=60
                result.append("一次出太多会刷屏\n先丢你一个卡组的份哦…")
            ct=cdb.getRandomNames(count=num,shrink=levels)
            name=ct[0]
            resultText="\n".join(ct)
    if not pr["pic"]:
        if pr.args.get("im",False):
            filename=str2greyPng(resultText,name)
            result.append(Image(filename) if not pr["reload"] else Image(filename,cache=False))
        else:
            result.append(resultText)
    return result

Events.onCmd("ydpic")(redirect("ygodraw",[CONS,"-pic"],ygodraw))

@Events.onCmd("logodraw")
def logodraw(pr:ParseResult):
    pr.command="yd"
    pr.args["n"]=20
    pr.args["notoken"]=True
    result=ygodraw(pr)
    msg:Message=pr.raw
    if msg.mtype==MessageType.Private:
        name=msg.getSrcName()
    else:
        name=f"[CQ:at,qq={msg.realSrc}]"
    result[-1]=f"{name}的卡：\n"+result[-1]
    return result

@Events.onNotCmd
def notCmd(pr:ParseResult, cp:CommandParser):
    msg:Message=pr.raw
    if msg and msg.content:
        part:MessagePart=msg.content[-1]
        text=part.brief
        if text.endswith(("!","！")):
            text=text.strip("！!").lower()
            if text.endswith(("抽卡","ドロー","draw")):
            # if text.lower().endswith(("抽卡！","ドロー！","draw!")):
                # 以 抽卡！结尾 抽一张卡图
                pr.args["pic"]=True
                pr.args["n"]=0
                pr.output.append(ygodraw(pr))

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

def initDuel(data:YGOConfig|None):
    YGORoom.initDuel(ygodir, data.servers if data and data.servers else {})
        

@Events.onCmd("duel")
def duel(pr:ParseResult):
    msg:Message=pr.raw
    result=[]
    room=None
    pr.args["me"]=pr.args.get("me") or not pr.params
    isMe=pr["me"]
    paramStr=pr.paramStr.strip()

    if not pr["random"]:
        key=pr.getByType("get") or (msg.realSrc if pr["me"] else paramStr) # -get key | -me | .duel key
        room=YGORoom.getMemberRoom(key)
        if not room and isinstance(key,str): # 没找到的话尝试处理 @
            keyContent=Content(key)
            if len(keyContent)==1:
                cqkey=keyContent[0]
                if isinstance(cqkey,At) and cqkey.qq.isdigit(): # -get @xx | .duel @xx
                    key=int(cqkey.qq) # 得到 @ 对象的 qq
                    isMe=isMe or key==msg.realSrc
                    room=YGORoom.getMemberRoom(key) # 再试着用 qq 找
    if not room:
        room=YGORoom.parseRoom(paramStr)
    noRoom=not room.name
    if isMe and noRoom and not pr["get"] and not pr["random"]:
        result.append("""看样子还没有记录自己的房间？\n这里是一个随机房间哦\n可以使用 .duelset xxx 记录自己的房间""")
    if noRoom or pr["random"]:
        room.name=YGORoom.randomRoomName(pr.parserData["mc"].data["ygocdb"])
    if pr.getByType("time",None,bool) or pr["tm0"] or noRoom: # -tm -> -tm 0  没房间的时候默认也建一个 TM0 的
        pr.args["time"]="0"
    room.args2prefix(pr.args)
    result.append(room.full)

    if not pr["server"]:
        for s in ("23333","233","2333"):
            if pr[s]:
                pr.args["server"]=s
    if pr["server"]: # 只有 -s 的时候才有服务器
        if isinstance(pr["server"],str) or not room.hasServer: # -s 有值时覆盖 room 记录的服务器
            room.serverName=pr.getByType("server","2333") # server是True的话默认2333
        if room.server:
            result.append(room.server)

    if pr["set"]:
        key=pr.getByType("set",msg.realSrc) #无值的场合使用QQ号
        srcName=msg.getSrcName()
        if room.full:
            YGORoom.saveMemberRoom(key,room,srcName)
            if not isinstance(key,str):
                key=None
            name=At(msg.realSrc).CQcode
            if msg.mtype==MessageType.Private:
                name=srcName
            result.append(YGORoom.hint("记录",key,name))

    if pr["del"]:
        key=pr.getByType("del",msg.realSrc)
        if YGORoom.removeMemberRoom(key):
            if not isinstance(key,str):
                key=None
            name=At(msg.realSrc).CQcode
            if msg.mtype==MessageType.Private:
                name=msg.getSrcName()
            result=[YGORoom.hint("移除",key,name)] # 移除的时候不发送房间
        else:
            result=["那个房间…本来就不存在哦…"] # 移除的时候不发送房间

    return result

Events.onCmd("duelset")(redirect("duel",[CONS,"-set"],duel))
Events.onCmd("dueldel")(redirect("duel",[CONS,"-del"],duel))

@Events.onCmd("server")
def server(pr:ParseResult):
    if pr["l"]:
        if YGORoom.servers:
            srvlist=("  ".join([name,srv[0],str(srv[1])]) for name,srv in YGORoom.servers.items()) # 服务器名  地址  端口
            return ["\n".join(srvlist)]
        else:
            return ["竟然没有任何服务器信息！？"]
    result=[]
    room=YGORoom()
    if not pr.params:
        pr.params.append("2333")
    for name in pr.params:
        room.serverName=name
        if room.server:
            result.append(room.server)
            room._host,room._port=None,None # 重置内部信息
    if result:
        return result
    return ["没找到对应的服务器…"]

# doneKW=["和了","胡了","自摸","ロン","ツモ"]

@Events.onCmd("mahjong")
def mahjong(pr:ParseResult):
    text=pr.paramStr
    # pr.args["和"]=pr["和"] or any(k in text for k in doneKW)
    #if pr["和"]:
    #    return [麻将.和()]
    num=pr.getToType("n",None,int)
    if text.isdigit():
        num=int(text)
    if isinstance(num,int):
        num=max(num,1)
        if num>= len(麻将.山):
            return [麻将.山]
        return [麻将.抽(num)]
    else:
        return [麻将.和()]

class FontUnit(Pattern):
    """
    各种字体文件
    路径例：font/file.ttf
    """

# =Config.Unit("font",str, doc="各种字体文件\n路径例：font/file.ttf")
FontUnit.addDefault("normal","")
FontUnit.addDefault("AA","")
FontUnit.addDefault("tex","")
# FontConfig["normal"]=""
# FontConfig["AA"]=""
# FontConfig["tex"]=""

PluginUnits.addDefault("font",annotation=FontUnit)

# @Config("font.toml").withDefaults(FontUnit).on
@pluginConfig.on
def initFont(config:dict[str,dict], bot:Bot):
    if data:=config.get("font"):
        initNormalFont(data.get("normal"))
        initAAFont(data.get("AA"))
        initTexFont(data.get("tex"))

# def initFont(bot:Bot):
#     paths=bot.config.get("font")
#     if paths:
#         initNormalFont(paths.get("normal"))
#         initAAFont(paths.get("AA"))
#         initTexFont(paths.get("tex"))

@Events.onCmd("AA")
async def drawAA(pr:ParseResult):
    if not AAMZ.files:
        await AAMZ.init()
    AAtext,file=await AAMZ.randomAA(hasR18=pr["R18"])
    AAimg=AA2img(AAtext)
    title=f"{file.dir}/{file.name}"
    imgTitle=title.strip(" /").replace("/","-")+str(random.randint(0,9)) # 文件名尾部加一位随机数字
    path=getImgPath(imgTitle,None)
    AAimg.save(path)
    return [ Content(title,Image(path)) ]

def asGen(val):
    if isinstance(val,(list,tuple)):
        yield from val
    elif isinstance(val,str):
        yield val

builderMap={
    "race":"race","attr":"attribute","type":"cardType","level":"level","rank":"rank","link":"link","P":"Pmark","atk":"attack","def":"defence","atk+def":"atkDefSum","id":"id"
}

@Events.onCmd("ygocdb")
def ygocdb(pr:ParseResult):
    cdb:cdbReader=pr.parserData["mc"].data["ygocdb"]
    conf:confReader=pr.parserData["mc"].data["ygoconf"]
    builder=SQLBuilder()
    paramStr=pr.paramStr
    if paramStr.strip():
        builder.keyword(*pr.params)
    for k,v in builderMap.items():
        val=pr[k]
        if val:
            getattr(builder,v)(*asGen(val))
    if pr["atk=def"]:
        builder.atkEqDef()
    if not builder.materials:
        return ["空气怎么查啊！"]
    foundSet=set()
    found:list[Card]=[]
    with cdb:
        directSearch=cdb.getCardsByName(paramStr)
        if directSearch:
            for ct in directSearch:
                c=Card()
                c.fromCDBTuple(ct,conf.setdict,conf.lfdict)
                foundSet.add(c.alias or c.id)
                found.append(c)
        builderSearch=cdb.getCardsByBuilder(builder,num=100)
        if builderSearch:
            for ct in builderSearch:
                c=Card()
                c.fromCDBTuple(ct,conf.setdict,conf.lfdict)
                if (c.alias or c.id) not in foundSet:
                    found.append(c)
    foundName:list[str]=[c.name+"\n" for c in found]
    if not foundName:
        return ["找不到卡片的说……"]
    foundName[-1]=foundName[-1].rstrip()
    page=pr.getToType("page",1,int)
    if pr["im"]:
        filename=str2greyPng("".join(foundName),foundName[0].rstrip())
        return [Image(filename)]
    return [CommandHelper().getPageContent(foundName,page)]

itemSplitter=re.compile(r"[\/、\\，\,\|;；]") # \ / 、 , ， | ; ；

Command("choose").names("choice","选择","选","抽","挑","帮我决定")

@Events.onCmd("choose")
def choose(pr:ParseResult):
    if not pr.params:
        return [random.choice(["听天由命","顺其自然","无中生有","空气","　"])]
    params=[item for item in pr.params if item!="\n"]
    if len(params)==1:
        paramList=[]
        partNum=0
        partList=[]
        for part in Content(pr.paramStr):
            if isinstance(part,Text):
                paramList.append(part.CQcode)
            else:
                paramList.append(f"{{{partNum}}}")
                partNum+=1
                partList.append(part.CQcode)
        paramStr="".join(paramList)
        # print(paramStr)
        # print(random.choice(itemSplitter.split(paramStr)).format(*partList))
        return [random.choice(itemSplitter.split(paramStr)).format(*partList)]
    return [random.choice(params)]

Command("tex").names("TEX","Tex","TeX")
@Events.onCmd("tex")
async def tex(pr:ParseResult):
    if not pr.params:
        return ["没有公式，texy啦!"]
    msg:Message=pr.raw
    content=Content(pr.paramStr)
    return [Image(await atext2img(CQunescape(content.plainText)))]

@Events.onCmd.error("tex")
def texError(pr:ParseResult,e:Exception):
    if isinstance(e,LatexError):
        return [" ".join(e.args)]
    raise e

# @Events.on(EventNames.Startup)
# def botStartUP(bot:Bot):
#     copyYGO(bot)
    # initFont(bot)

@Events.on(EventNames.MsgCoreInit)
def coreInit(core:MCore):
    # initYGO(core)
    # YGORoom.initDuel(ygodir,core.bot.config.get("ygo",{}).get("servers",{}))
    initEat(core)
    initLuck(core)

@Events.on(EventNames.Shutdown)
def botShutDown(bot:Bot):
    YGORoom.saveDuel()

# c.showHelp=True
# print(c.getHelp())
