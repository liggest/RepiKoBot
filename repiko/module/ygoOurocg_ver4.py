#coding:utf-8
# import sqlite3
# import configparser
import json

from urllib import request
from urllib import parse
from bs4 import BeautifulSoup

from .ygo.card import Card,CardAttribute,CardRace,CardType,LinkMark

class ourocg():

    def __init__(self):
        #config = configparser.ConfigParser()
        #config.read('setting.ini')
        #self.path=config["ygo"]["ygopath"]
        self.edition=2

    def SetTranslateEdition(self,ed):
        if ed.lower()=="cn":
            self.edition=0
        elif ed.lower()=="nw":
            self.edition=1

    def FindCardByName(self,searchtext):
        #result="找不到卡片的说……"
        url=r"https://www.ourocg.cn/search/{k}"
        kw =searchtext
        #cn=kw
        kw=parse.quote(kw)
        encode_url=url.format(k=kw)
        #print(encode_url)
        req=request.urlopen(encode_url)
        raw_html=req.read().decode("utf8")
        html=BeautifulSoup(raw_html,"lxml")
        targeturl=""
        Pmark=[]
        if html.find_all("title")[0].string.startswith("搜索"):
            scripts=html.find_all("script")
            for s in scripts:
                if(str(s.string).strip().startswith("window.__STORE__")):
                    targets=str(s.string[s.string.find("{"):]).strip()[:-1]
                    carddata=json.loads(targets)
                    sts=searchtext.strip()
                    for tar in carddata["cards"]:
                        if tar["name"]== sts or tar["name_nw"]==sts or tar["name_ja"]== sts or tar["name_en"]== sts:
                            targeturl=tar["href"].replace("\\","")
                            Pmark=[tar.get("pend_l",None),tar.get("pend_r",None)]
                            #print(Pmark)
                    if targeturl=="" and len(carddata["cards"])!=0:
                        tar=carddata["cards"][0]
                        targeturl=tar["href"].replace("\\","")
                        Pmark=[tar.get("pend_l",None),tar.get("pend_r",None)]
                    #print(targeturl)
                    break
        else:
            targeturl=encode_url
        if targeturl!="":
            encode_url=targeturl
            req=request.urlopen(encode_url)
            raw_html=req.read().decode("utf8")
            #print(encode_url)
            html=BeautifulSoup(raw_html,"lxml")
            isRD=False
            if html.find("div",{"class":"rd-mark"}):
                isRD=True
            div=html.find_all("div",{"class":"val"})
            divr=[[y for y in x.stripped_strings] for x in div]
            #print(divr)
            cardtypes=divr[3]
            c=Card(cardtypes)
            if c.isLink:
                linkmark=html.find("div",{"class":"linkMark"})
                for mark in linkmark.find_all("i"):
                    temp=mark["class"][1].split("_")
                    if temp[2]=="on":
                        c.linkmark.add( LinkMark.fromNumber(int(temp[1]),True) )
            c.name=divr[0][self.edition]
            jpname=divr[1][0]
            if jpname!="-":
                c.jpname=jpname.replace("・","·")
            enname=divr[2][0]
            if enname!="-":
                c.enname=enname
            c.isRD=isRD
            c.id=divr[4][0]
            limitnum=5
            if isRD:
                limitnum=4
            c.limit=divr[limitnum][0]
            otnum=limitnum+1
            if divr[otnum]: #如果是OCG/TCG专有
                c.ot=divr[otnum][0]
            effectnum=-1
            if c.isMonster:
                c.race=CardRace.fromStr(divr[otnum+1][0])
                c.attribute=CardAttribute.fromStr(divr[otnum+2][0])
                if c.isXyz:
                    c.rank=ourocg.dealInt(divr[otnum+3][0])
                    c.level=c.rank
                if c.isP:
                    c.Pmark=Pmark
                if c.isLink:
                    c.linknum=ourocg.dealInt(divr[otnum+5][0])
                    c.level=c.linknum
                    c.attack=ourocg.dealInt(divr[otnum+4][0])
                else:
                    c.level=ourocg.dealInt(divr[otnum+3][0])
                    c.attack=ourocg.dealInt(divr[otnum+4][0])
                    c.defence=ourocg.dealInt(divr[otnum+5][0])
            L=len(divr[effectnum])
            tempString=divr[effectnum][-1]
            effectlist=[0]
            for x in range(-2,-1*(L+1),-1):
                if divr[effectnum][x]==tempString:
                    tempnum=-1-x
                    effectlist.append(L-2*tempnum)
                    effectlist.append(effectlist[1]+tempnum)
                    effectlist.append(effectlist[2]+tempnum)
            effects=divr[effectnum][effectlist[self.edition]:effectlist[self.edition+1]]
            effectText="\n".join(effects)
            c.effect=ourocg.beautifyText(effectText)
            return c
        return None

    def getWikiLink(self,card):
        if card.jpname:
            pageword=f"《{ourocg.towikistr(card.jpname)}》"
        elif card.enname:
            pageword=f"《{card.enname}》"
        else:
            return None
        pageword=parse.quote(pageword,encoding="euc-jp")
        return r"https://yugioh-wiki.net/index.php?cmd=read&page="+pageword

    @staticmethod
    def towikistr(text):
        """半角转全角，以及一些特殊符号的转换"""
        transDict={
            #' ':chr(12288), #半角空格直接转化
            '·':'・',
            '－':'−',
            "Ⅰ":"Ｉ",
            "Ⅱ":"ＩＩ",
            "Ⅲ":"ＩＩＩ",
            "Ⅳ":"ＩＶ",
            "Ⅴ":"Ｖ",
            "Ⅵ":"ＶＩ",
            "Ⅶ":"ＶＩＩ",
            "Ⅷ":"ＶＩＩＩ",
            "Ⅸ":"ＩＸ",
            "Ⅹ":"Ｘ",
            "Ⅺ":"ＸＩ",
            "Ⅻ":"ＸＩＩ"
        }
        r = ""
        for c in text:
            trans=transDict.get(c,None)
            if trans:
                c=trans
            else:
                oc=ord(c)
                if oc > 32 and oc <= 126:  #半角字符（除空格）根据关系转化
                    c=chr(oc+65248)
            r += c
        return r

    @staticmethod
    def dealInt(text):
        if text.isdigit():
            return int(text)
        else:
            return text

    @staticmethod
    def beautifyText(text):
        """试着给效果文本加换行，好看一点"""
        nums=set(list("①②③④⑤⑥⑦⑧⑨⑩●"))
        transDict={"・":"·"}
        r = ""
        l=len(text)
        for i,c in enumerate(text):
            trans=transDict.get(c,None)
            if trans:
                c=trans
            elif c in nums:
                if 1<i<l-1 and text[i-1]!="\n" and text[i+1]=="：":
                    c="\n"+c
            r+=c
        return r


if __name__ == "__main__":
    text=input()
    a=ourocg()
    print(a.FindCardByName(text))
