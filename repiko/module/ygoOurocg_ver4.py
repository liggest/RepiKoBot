#coding:utf-8
# import sqlite3
# import configparser
import json

from urllib import request
from urllib import parse
import httpx
from bs4 import BeautifulSoup
from bs4.element import NavigableString,CData
try:
    from bs4.element import TemplateString #新版bs4需要
except:
    TemplateString=NavigableString

from .ygo.card import Card,CardAttribute,CardRace,CardType,LinkMark

class ourocg():

    def __init__(self):
        self.edition=2

    def SetTranslateEdition(self,ed):
        if ed.lower()=="cn":
            self.edition=0
        elif ed.lower()=="nw":
            self.edition=1

    ourocgLink=r"https://www.ourocg.cn/"

    def GetHTML(self,url):
        res=httpx.get(url)
        return res.text

    def GetCardHTMLWithJ(self,searchtext,url,searchHTML):
        targeturl=""
        cardJson=None
        # Pmark=[None,None]
        html=BeautifulSoup(searchHTML,"lxml")
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
                            cardJson=tar
                            # Pmark=[tar.get("pend_l",None),tar.get("pend_r",None)]
                            #print(Pmark)
                    if targeturl=="" and len(carddata["cards"])!=0:
                        tar=carddata["cards"][0]
                        targeturl=tar["href"].replace("\\","")
                        cardJson=tar
                        # Pmark=[tar.get("pend_l",None),tar.get("pend_r",None)]
                    #print(targeturl)
                    break
        else:
            targeturl=url
        return targeturl,cardJson

    def GetCardFromHTML(self,cardHTML,cardJson):
        # print(cardJson)
        html=BeautifulSoup(cardHTML,"lxml")
        isRD=False
        if html.find("div",{"class":"rd-mark"}):
            isRD=True
        div=html.find_all("div",{"class":"val"})
        # divr=[[y for y in x.stripped_strings] for x in div]
        divr=[[y for y in x._all_strings(True,types=(NavigableString,CData,TemplateString))] for x in div]
        # 类似 stripped_strings，但新版本需要纳入 TemplateString 才能效果一致
        # print(divr)
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
        c.img=cardJson["img_url"]
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
                # c.Pmark=Pmark
                c.Pmark=[cardJson.get("pend_l",None),cardJson.get("pend_r",None)]
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

    def FindCardByName(self,searchtext):
        url=f"{self.ourocgLink}search/{searchtext}"
        searchHTML=self.GetHTML(url)
        targeturl,cardJson=self.GetCardHTMLWithJ(searchtext,url,searchHTML)
        if targeturl:
            cardHTML=self.GetHTML(targeturl)
            return self.GetCardFromHTML(cardHTML,cardJson)
        return None

    async def AsyncGetHTML(self,url):
        async with httpx.AsyncClient() as client:
            res=await client.get(url)
        return res.text

    async def AsyncSearchByName(self,searchtext):
        url=f"{self.ourocgLink}search/{searchtext}"
        searchHTML=await self.AsyncGetHTML(url)
        targeturl,cardJson=self.GetCardHTMLWithJ(searchtext,url,searchHTML)
        if targeturl:
            cardHTML=await self.AsyncGetHTML(targeturl)
            return self.GetCardFromHTML(cardHTML,cardJson)
        return None

    wikiLink=r"https://yugioh-wiki.net/"

    def getWikiLink(self,card):
        if card.jpname:
            pageword=f"《{ourocg.towikistr(card.jpname)}》"
        elif card.enname:
            pageword=f"《{card.enname}》"
        else:
            return None
        pageword=parse.quote(pageword,encoding="euc-jp")
        return f"{self.wikiLink}index.php?cmd=read&page={pageword}"

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
    # text=input()
    # a=ourocg()
    # print(a.FindCardByName(text))

    
    async def main():
        text=input()
        a=ourocg()
        print(await a.AsyncSearchByName(text))

    import asyncio
    asyncio.run(main())
    

