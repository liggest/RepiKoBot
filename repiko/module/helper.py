#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

class Helper():
    def __init__(self,hpath):
        self.helpPath=hpath
        self.linenum=10
    
    cmdShorthand={
        "yc":"ygocard",
        "eat":"canteen",
        "cal":"calculate",
        "r":"roll",
        "ys":"ygoserver",
        "ts":"translate",
        "?":"help",
        "？":"help",
        "jrrp":"luck",
        "yd":"ygodraw",
        "抽卡":"ygodraw",
        "aw":"aword",
        "一句话":"aword",
        "一言":"aword",
        "猫":"cat"
        }

    def getHelp(self,target=[],page=1):
        for i in range(len(target)):
            t=self.cmdShorthand.get(target[i],None)
            if not t is None:
                target[i]=t
        path=os.path.join(self.helpPath,*target)
        #print(os.path.abspath('.'))
        if os.path.exists(path+".txt"):
            filepath=path+".txt"
            print(filepath)
        else:
            filepath=os.path.join(path,"general.txt")
            if not os.path.exists(filepath):
                return ["是没见过的帮助呢"]
        r=self.getFileResult(filepath,page)
        return [r]

    def readFile(self,filepath):
        result=[]
        with open(filepath,"r",encoding="utf8") as f:
            result=f.readlines()
        return result

    def fileClipper(self,fresult):
        l=len(fresult)
        result=[]
        for i in range(0,l,self.linenum):
            lm=l-i
            if lm>=self.linenum/2:
                result.append("".join(fresult[i:i+self.linenum]))
            else:
                if result==[]:
                    result.append("".join(fresult[-lm:]))
                else:
                    result[-1]+="".join(fresult[-lm:])
        result[-1]+="\n"
        return result

    def addPage(self,fcresult):
        l=len(fcresult)
        if l<2:
            return fcresult,l
        for i in range(l):
            p="===%d/%d==="%(i+1,l)
            fcresult[i]+=p
        return fcresult,l

    def getFileResult(self,filepath,page=1):
        r,l=self.addPage(self.fileClipper(self.readFile(filepath)))
        index=page-1
        if index>=l:
            return r[l-1]
        elif index<=0:
            return r[0]
        return r[index]


if __name__=="__main__":
    h=Helper("./help")
    #print(h.getHelp()[0])
    #print(h.getHelp(page=2)[0])
    #print(h.getHelp(page=3)[0])
    print(h.getHelp(["hello"])[0])
    #print(h.getHelp(["ygocard"],page=2)[0])