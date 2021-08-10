
class RequestData:

    rTypeMap={"friend":"user_id","group":"group_id"}

    @classmethod
    def getSrcList(cls,j):
        rt=j["request_type"]
        if rt!="friend":
            return [j[cls.rTypeMap[rt]],j["user_id"]]
        return [j["user_id"]]

    def __init__(self,flag,rtype="friend",subtype:str=None):
        self.content=""
        self.srcList=[0]
        self.dst=0
        self.flag=flag
        self.rtype=rtype
        if subtype:
            self._subtype=subtype
        elif self.isGroupReq():
            self._subtype="invite" # 默认是invite
        else:
            self._subtype=""
        self.approve=False
        self.response=""

    def __str__(self):
        result=f"来自 {self.realSrc} 的"
        if self.isGroupReq():
            if self.isGroupAdd():
                result+=f"加群 {self.src} 请求"
            elif self.isGroupInvite():
                result+=f"群 {self.src} 邀请"
        elif self.isFriendReq():
            result+="加好友请求"
        result+="\n"
        result+=f"验证信息：{self.content}\n"
        result+=f"flag：{self.flag}"
        return result

    @classmethod
    def fromJSON(cls,j):
        req=RequestData(j["flag"])
        req.json=j
        req.rtype=j["request_type"]
        req.dst=j["self_id"] # 接收者是自己
        req.srcList=cls.getSrcList(j)
        req.content=j["comment"]
        req._subtype=j.get("sub_type","")
        return req

    @property
    def subtype(self):
        if self._subtype:
            return self._subtype # add invite
        return self.rtype # friend

    @property
    def src(self):
        """
            群聊 - 群号\\
            私聊 - 发送者的QQ
        """
        return self.srcList[0]

    @property
    def realSrc(self):
        """
            发送者的QQ
        """
        return self.srcList[-1]

    def isFriendReq(self) -> bool:
        return self.rtype=="friend"

    def isGroupReq(self) -> bool:
        return self.rtype=="group"

    def isGroupAdd(self) -> bool:
        return self.subtype=="add"
    
    def isGroupInvite(self) -> bool:
        return self.subtype=="invite"

    def setResponse(self,approve=True,response:str=None):
        if response:
            self.response=response
        self.approve=approve

    def addQuickResponse(self,approve=True,response:str=None):
        self._quickResponse=True
        self.setResponse(approve,response)
        # self.resj={}
        # self.resj["approve"]=approve
        # if not approve and self.rtype=="group":
        #     self.resj["reason"]=response # 拒绝理由
        # elif approve and self.rtype=="friend":
        #     self.resj["remark"]=response # 好友备注

    @property
    def quickResponse(self):
        return getattr(self,"_quickResponse",False)

    @property
    def resj(self):
        param={}
        param["approve"]=self.approve
        if self.response:
            if not self.approve and self.isGroupReq():
                self.resj["reason"]=self.response # 拒绝理由
            elif self.approve and self.isFriendReq():
                self.resj["remark"]=self.response # 好友备注
        return param

    @property
    def sendParam(self):
        param=self.resj
        param["flag"]=self.flag
        if self.isGroupReq():
            param["sub_type"]=self.subtype
        return param