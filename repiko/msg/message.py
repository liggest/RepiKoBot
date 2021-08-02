

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
        msg.dst=j["self_id"]
        msg.srcList=cls.getSrcList(j)
        msg.content=j["message"]
        msg.id=j["message_id"]
        return msg

    def __init__(self,dst=0,mtype="private",*msgs):
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
        return self.srcList[0]

    @property
    def realSrc(self):
        return self.srcList[-1]

    def srcAsDst(self):
        msg=copy.copy(self)
        msg.dst=self.src
        msg.srcList=[self.dst]
        return msg
    
    def addQuickResponse(self,reply,atSender=True):
        self.quickResponse=True
        self.resj={}
        self.resj["reply"]=str(reply)
        if self.mtype=="group" or self.mtype=="discuss":
            self.resj["at_sender"]=atSender



    # def copy(self):
    #     msg=Message()
    #     msg.content=self.content
    #     msg.src=self.src.copy()
    #     msg.dst=self.dst
    #     msg.id=self.id
    #     msg.mtype=self.mtype
    #     return msg


