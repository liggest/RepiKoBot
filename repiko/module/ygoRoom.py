import os
import yaml
import random

from .ygo.dataloader import cdbReader

class YGORoom:

    ygodir=""

    roomFile="MemberRoom.yaml"
    memberRooms={}
    servers={}

    boolCodeMap={"match":"M","tag":"T","tcg":"TO","ot":"OT","nolflist":"NF","nounique":"NU","nocheck":"NC","noshuffle":"NS","ai":"AI"}
    intCodeMap={
        "lp":("LP",(1,99999,8000)),
        "time":("TM",(0,999,3)),
        "start":("ST",(1,40,5)),
        "draw":("DR",(0,35,1)),
        "lflist":("LF",(1,99999,1)),
        "rule":("MR",(1,5,5))
    }
    # intRangeMap={"lp":(1,99999,8000),"time":(0,999,3),"start":(1,40,5),"draw":(0,35,1),"lflist":(1,99999,1),"rule":(1,5,5)} 
    # (下限，上限，默认值) 禁卡表数量一直在变化，故不设上限

    roomSuffix=("坊","村","城","现实","屋","居室","空间","的房","之间")

    @classmethod
    def initDuel(cls,ygodir,servers):
        roomFilePath=os.path.join(ygodir,cls.roomFile)
        if os.path.exists(roomFilePath):
            with open(roomFilePath,encoding="utf-8") as f:
                cls.memberRooms=yaml.safe_load(f)
        cls.servers=servers
        cls.ygodir=ygodir

    @classmethod
    def saveDuel(cls):
        if not cls.memberRooms:
            return
        roomFilePath=os.path.join(cls.ygodir,cls.roomFile)
        with open(roomFilePath,"w",encoding="utf-8") as f:
            yaml.safe_dump(cls.memberRooms,f,encoding="utf-8",allow_unicode=True)

    @classmethod
    def parseRoom(cls,roomText:str):
        prefix=set()
        *prefixList,name=roomText.split("#")
        if prefixList:
            prefix.update(prefixList[0].split(","))
            name="#".join(prefixList[1:]+[name])
        return YGORoom(name,prefix)

    @classmethod
    def getMemberRoom(cls,key):
        roomInfo:dict=cls.memberRooms.get(key)
        if roomInfo:
            room=cls.parseRoom(roomInfo["room"])
            room.serverName=roomInfo.get("server")
            return room
        return None

    @classmethod
    def saveMemberRoom(cls,key,room:"YGORoom",name=None):
        info=room.roomInfo
        if name:
            info["name"]=name
        cls.memberRooms[key]=info

    @classmethod
    def removeMemberRoom(cls,key):
        if key in cls.memberRooms:
            cls.memberRooms.pop(key)

    @classmethod
    def hint(cls,action="记录",key=None,name=None):
        if key:
            return f"{action}了房间【{key}】"
        if name:
            return f"{action}了{name}的房间"
        return f"{action}了房间"


    def __init__(self,name=None,prefix=None):
        self.prefix=prefix or set()
        self.name=name or ""
        self.serverName=""
        self._host=None
        self._port=None

    def randomRoomName(self,cdb:cdbReader):
        result=[]
        with cdb:
            ct=cdb.getRandomNames(count=random.randint(1,4))
            result=[random.choice(n) for n in ct]
        self.name="".join(result)+random.choice(self.roomSuffix)
        return self.name

    def togglePrefix(self,code):
        if code in self.prefix:
            self.prefix.remove(code)
        else:
            self.prefix.add(code)

    def args2prefix(self,args:dict):
        for arg in args:
            code=self.boolCodeMap.get(arg)
            if code:
                self.togglePrefix(code)
            else:
                code=self.intCodeMap.get(arg)
                if code:
                    code,intRange=code
                    minVal,maxVal,defaultVal=intRange
                    val=args.get(arg)
                    if val is not None:
                        if isinstance(val,str) and val.isdigit():
                            val=int(val)
                        val=max(minVal,val)
                        val=min(maxVal,val)
                        prefix=f"{code}{val}"
                        self.togglePrefix(prefix)
                        for p in [p for p in self.prefix if p.startswith(code) and p!=prefix]:
                            self.prefix.remove(p)

    def server2HostPort(self):
        noserver=(None,None)
        if self.serverName.startswith("233"):
            host,port=self.servers.get("233",noserver)
            port=int(f"2{'3'*self.serverName.count('3')}")
        elif self.serverName.endswith("编年史"):
            host,port=self.servers.get("编年史",noserver)
        elif self.serverName=="2pick" or self.serverName=="轮抽":
            host,port=self.servers.get("2pick",noserver)
        elif self.serverName.startswith("复读") or self.serverName.lower()=="repiko":
            host,port=self.servers.get("repiko",noserver)
        else:
            host,port=noserver
        self._host,self._port=host,port

    @property
    def hasServer(self):
        return self.host and self.port

    @property
    def full(self):
        if self.prefix:
            return f"{','.join(self.prefix)}#{self.name}"
        return self.name

    @property
    def server(self):
        if self.hasServer:
            return f"{self.host}  {self.port}"
        return ""

    @property
    def host(self):
        if not self._host and self.serverName:
            self.server2HostPort()
        return self._host

    @property
    def port(self):
        if not self._port and self.serverName:
            self.server2HostPort()
        return self._port
        

    @property
    def roomInfo(self):
        return {
            "room":self.full,
            "server":self.serverName
        }