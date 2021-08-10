

import copy


class Message:
    
    mTypeMap={"private":"user_id","group":"group_id","discuss":"discuss_id"}

    @classmethod
    def getSrcList(cls,j):
        mt=j["message_type"]
        if mt!="private":
            return [j[cls.mTypeMap[mt]],j["user_id"]]
        return [j["user_id"]]

    @classmethod
    def fromJSON(cls,j):
        msg=Message()
        msg.json=j
        msg.mtype=j["message_type"]
        msg.dst=j["self_id"] # 接收者是自己
        msg.srcList=cls.getSrcList(j)
        msg.content=j["message"]
        msg.id=j["message_id"]
        return msg

    def copy(self,srcAsDst=False):
        """
            浅拷贝一个 msg 对象 \n
            srcList 会被额外拷贝 \n 
            srcAsDst 默认为 False 若为 True 则复制对象的 src 和 dst 调转
        """
        msg=copy.copy(self)
        if srcAsDst:
            msg.dst=self.src
            msg.srcList=[self.dst]
        else:
            msg.srcList=self.srcList.copy()
        return msg

    def __init__(self,*msgs,dst=0,mtype="private"):
        self.content="\n".join(msgs)
        self.srcList=[0]
        self.dst=dst
        self.id=0
        self.mtype=mtype

    def __str__(self):
        return self.content

    @property
    def mtype2key(self):
        return self.mTypeMap[self.mtype]

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

    @property
    def isMe(self):
        return self.dst == self.realSrc # 接收者和发送者是同一位，说明是收到了自己的发言

    @property
    def sendParam(self):
        return {"message":self.content,self.mtype2key:self.dst}
    
    def addQuickResponse(self,reply,atSender=True):
        self._quickResponse=True
        self.resj={}
        self.resj["reply"]=str(reply)
        if self.mtype=="group" or self.mtype=="discuss":
            self.resj["at_sender"]=atSender

    @property
    def quickResponse(self):
        return getattr(self,"_quickResponse",False)

    def clearAtMe(self):
        atcode=f"[CQ:at,qq={self.dst}]"
        if atcode in self.content:
            self.content=self.content.replace(atcode,"")
            self._atMe=True
        else:
            self._atMe=False
    
    @property
    def hasAtMe(self):
        """
            消息内容中是否有@到bot
        """
        return getattr(self,"_atMe",False)
    
    @property
    def isReply(self):
        """
            消息是否是个回复
        """
        return self.content.lstrip().startswith("[CQ:reply")

    def getSrcName(self):
        name=None
        if hasattr(self,"json"):
            sender=self.json.get("sender")
            if sender:
                name=sender.get("nickname")
        return name

    def getSrcCard(self):
        card=None
        if not hasattr(self,"json") or not self.mtype=="group":
            return None
        sender=self.json.get("sender")
        if sender:
            card=sender.get("card")
        return card
