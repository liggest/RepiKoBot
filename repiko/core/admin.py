#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from LSparser import CommandParser,ParseResult


class ACore():
    def __init__(self,bot):
        self.AdminMode=False
        self.bot=bot

    ModeText={False:"OFF",True:"ON"}
    
    def GetAdminResponse(self,content):
        cp=CommandParser()
        pr=cp.getCommand(content)
        if pr:
            cmd=pr.command
            if cmd=="admin":
                pr.parse()
                if len(pr.params)==0:
                    return ["没有参数可不行啊…"]
                else:
                    return self.AdminStuff(pr.params[0],*pr.params[1:])
            elif cmd=="broadcast":
                pr.opt(["--qq","-qq"],1).parse()
                qqg=pr.args.get("qq",None)
                if len(pr.params)==0:
                    return ["没有参数可不行啊…"]
                elif qqg is None:
                    return ["我不知道要广播给哪些群"]
                else:
                    msg=" ".join(pr.params)
                    if msg.strip()=="update":
                        msg=self.bot.update
                    bg=[]
                    if isinstance(qqg,list):
                        for x in qqg:
                            self.getBroadcastMembers(x,bg)
                    elif isinstance(qqg,str):
                        self.getBroadcastMembers(qqg,bg)          
                    self.bot.SendBroadcast(bg,msg,mt="group")
                    return ["向%d个群广播了消息"%(len(bg))]
            elif self.AdminMode:
                pr.parse()
                return self.AdminStuff(cmd,*pr.params)
            else:
                return []
        return []

    def getBroadcastMembers(self,qqinfo,group):
        qqs=self.bot.broadcastGroup.get(qqinfo,None)
        if not qqs is None:
            group+=qqs
        elif qqinfo.isdigit:
            group.append(int(qqinfo))

    def AdminStuff(self,cmd,*params):
        if cmd=="debug":
            self.bot.DebugMode=not self.bot.DebugMode
            return ["Debug:"+self.ModeText[self.bot.DebugMode]]
        elif cmd=="restart":
            self.bot.Restart(3000)
            return ["约3s后重启插件~"]
        elif cmd=="status" or cmd=="version":
            return [self.bot.GetStatus(stype=cmd)]
        elif cmd=="clean":
            if len(params)==0:
                return ["请指明需要清理的内容\nlog、image、record、show、bface"]
            else:
                result=[]
                for p in params:
                    ct=self.bot.Clean(p)
                    result.append("清理"+ct+"中…")
            return result
        elif cmd=="reload":
            if len(params)!=0:
                self.bot.Reload(params[0])
                return ["正在重载"+params[0]]
            else:
                self.bot.Reload()
            return ["正在重载…"]
        elif cmd=="on":
            self.AdminMode=True
            return ["Admin Mode:"+self.ModeText[self.AdminMode]]
        elif cmd=="off":
            self.AdminMode=False
            return ["Admin Mode:"+self.ModeText[self.AdminMode]]
        elif cmd=="mode":
            self.AdminMode=not self.AdminMode
            return ["Admin Mode:"+self.ModeText[self.AdminMode]]
        return []

if __name__=="__main__":
    pass