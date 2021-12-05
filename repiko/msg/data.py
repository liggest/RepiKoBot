from __future__ import annotations

# import copy
from collections.abc import Iterable

from repiko.core.constant import MessageType,RequestType,NoticeType,MetaEventType
from repiko.msg.part import At,Reply
from repiko.msg.content import Content
from repiko.msg.util import dictSetter

class BaseData(dict):
    """ 数据（事件）类基类 """

    _subs={}
    _typeClass={
        "message":MessageType,
        "request":RequestType,
        "notice":NoticeType,
        "meta_event":MetaEventType
    }

    @classmethod
    def __init_subclass__(subcls):
        # 创建子类时，按转为小写后的子类名记录子类（对应postType）
        subcls._subs[subcls.__name__.lower()]=subcls
        super().__init_subclass__()

    @classmethod
    def asSubClass(cls,pt:str) -> type:
        return cls._subs.get(pt)

    @classmethod
    def build(cls,dst=0) -> BaseData:
        """ 通过参数构建对象 """
        obj=cls()
        obj.dst=dst
        obj.realSrc=0
        # build 出来默认是为了发消息，只提供接收者(dst)即可
        return obj

    def __new__(cls,*args,**kw):
        if cls is BaseData and args and isinstance(args[0],dict): # 尽量避免创建基类，根据 post type 自动创建子类
            subcls=cls.asSubClass(args[0].get("post_type"))
            if subcls:
                return super().__new__(subcls,*args,**kw)
        return super().__new__(cls,*args, **kw)

    def __init__(self,*args,**kw):
        """ 数据（事件） \n\n 默认从 字典/JSON 创建 """
        self._dictInit=bool(args) and not isinstance(args[0],str) and isinstance(args[0],Iterable) 
        if self._dictInit:
            # 对象从可迭代对象中创建（字符串除外）
            super().__init__(*args,**kw)
        else:
            super().__init__()   # 初始化空字典
        self.quickReply=False
        self._content=None
        self._src=0
        self._dst=0

    def addQuickReply(self):
        """ 添加快速响应 """
        self.quickReply=True

    @property
    def replyJson(self) -> dict:
        """ 快速响应的 Json """
        return {}
    
    @property
    def postType(self) -> str:
        return self["post_type"]

    postType=postType.setter(dictSetter("post_type"))

    @property
    def dtype(self) -> str:
        """
            对应 {post_type}_type \n
            如 message_type、request_type
        """
        typeName=self.postType
        return self._typeClass.get(typeName,str)(self[f"{typeName}_type"]) # 如 MessageType(self["message_type"])

    @dtype.setter
    def dtype(self,val:str):
        self[f"{self.postType}_type"]=val

    @property
    def subtype(self) -> str:
        """ subtype \n\n 很可能没有 """
        return self.get("sub_type","")

    subtype=subtype.setter(dictSetter("sub_type"))

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self,val):
        self._content=val

    @property
    def realSrc(self) -> int:
        """
            发送者的QQ
        """
        return self.get("user_id")

    realSrc=realSrc.setter(dictSetter("user_id"))
    
    @property
    def src(self) -> int:
        """
            群聊 - 群号\n
            私聊 - 发送者的QQ
        """
        return self._src or self.realSrc

    @src.setter
    def src(self,val:int):
        self._src=val

    @property
    def dst(self) -> int:
        return self._dst or self["self_id"]

    @dst.setter
    def dst(self,val:int):
        self._dst=val

    @property
    def sendParam(self):
        """ 提供给 API 的参数 """
        return {}


class Message(BaseData):
    """ 消息 """

    dtypeMap={
        MessageType.Private:"user_id",
        MessageType.Group:"group_id",
        # "discuss":"discuss_id"
    }

    @classmethod
    def build(cls,content,dst=0,mtype=MessageType.Private) -> Message:
        # if not isinstance(content,Content):
        #     content=Content(content)
        obj:Message=super().build(dst)
        obj.content=content
        obj.mtype=mtype
        obj.id=0
        return obj

    def __init__(self,*args,**kw):
        """ 消息数据 \n\n 默认从 字典/JSON 创建 """
        super().__init__(*args, **kw)
        if self._dictInit:
            self._src:int=self[self.dtypeMap[self.mtype]] # "private" => self["user_id"]    "group" => self["group_id"]
            self["message"]=Content(self["message"])
        else:
            self.content=Content()
        self._hasAtMe=None

    def __str__(self):
        return str(self.content)

    @property
    def content(self):
        return self.get("message") or self._content

    @content.setter
    def content(self,val:Content):
        if not isinstance(val,Content):
            val=Content(val)
        self._content=val
        self["message"]=val

    @property
    def mtype(self) -> str:
        """ 等价于 dtype """
        return MessageType(self["message_type"])
    
    mtype=mtype.setter(dictSetter("message_type"))

    @property
    def id(self) -> int:
        return self["message_id"]

    id=id.setter(dictSetter("message_id"))
    
    def addQuickReply(self,reply:Content,atSender=True):
        if not isinstance(reply,Content):
            reply=Content(reply)
        super().addQuickReply()
        self._replyJson={}
        self._replyJson["reply"]=reply
        if self.mtype==MessageType.Group:
            self._replyJson["at_sender"]=atSender
    
    @property
    def replyJson(self) -> dict:
        if self.quickReply:
            return self._replyJson
        return {}

    @property
    def sendParam(self):
        return {"message":self.content,self.dtypeMap[self.mtype]:self.dst} # "user_id"/"group_id" : self.dst

    def copy(self,srcAsDst=False):
        """
            浅拷贝一个 msg 对象 \n
            但额外拷贝 content \n
            srcAsDst 若为 True 则复制对象的 src 和 dst 调转
        """
        msg=self.__class__(super().copy())
        msg.content=self.content.copy()
        if srcAsDst:
            msg.dst=self.src
            msg._src=None # 使 src 和 realSrc 等价
            msg.realSrc=self.dst
        return msg

    @property
    def isMe(self):
        return self.dst == self.realSrc # 接收者和发送者是同一位，说明是收到了自己的发言

    def clearAtMe(self):
        at=At(self.dst)
        count=self.content.removeAll(at)
        self._hasAtMe=bool(count)

    @property
    def hasAtMe(self) -> bool:
        """
            消息内容中是否有@到bot
        """
        return self._hasAtMe

    @property
    def isReply(self):
        """
            消息是否是个回复
        """
        return Reply in self.content

    def getSrcName(self):
        return self.get("sender",{}).get("nickname")
    
    def getSrcCard(self):
        return self.get("sender",{}).get("card")


class Request(BaseData):
    """ 请求 """

    dtypeMap={
        RequestType.Friend:"user_id",
        RequestType.Group:"group_id"
    }

    @classmethod
    def build(cls,flag,rtype=RequestType.Friend,subtype:str=None) -> Message:
        obj:Request=super().build(dst=0)
        obj.content=""
        obj.flag=flag
        obj.rtype=rtype
        if subtype:
            obj.subtype=subtype
        elif obj.isGroupReq:
            obj.subtype="invite" # 默认是invite
        # subtype 默认为 ""
        return obj

    def __init__(self,*args,**kw):
        """ 请求数据 \n\n 默认从 字典/JSON 创建 """
        super().__init__(*args, **kw)
        if self._dictInit:
            self._src:int=self[self.dtypeMap[self.rtype]] # "friend" => self["user_id"]    "group" => self["group_id"]
            # self.content:str=self["comment"]
        else:
            self.content=""
        self.approve=False
        self.response=""

    def __str__(self):
        result=f"来自 {self.realSrc} 的"
        if self.isGroupReq:
            if self.isGroupAdd:
                result+=f"加群 {self.src} 请求"
            elif self.isGroupInvite:
                result+=f"群 {self.src} 邀请"
        elif self.isFriendReq:
            result+="加好友请求"
        result+="\n"
        result+=f"验证信息：{self.content}\n"
        result+=f"flag：{self.flag}"
        return result

    @property
    def content(self):
        return self["comment"] or self._content

    @content.setter
    def content(self,val:Content):
        self._content=val
        self["comment"]=val

    @property
    def rtype(self) -> str:
        """ 等价于 dtype """
        return RequestType(self["request_type"])
    
    rtype=rtype.setter(dictSetter("request_type"))

    @property
    def flag(self) -> str:
        return self["flag"]

    flag=flag.setter(dictSetter("flag"))

    @property
    def subtype(self) -> str:
        return super().subtype or self.rtype

    subtype=subtype.setter(dictSetter("sub_type"))

    @property
    def isFriendReq(self) -> bool:
        return self.rtype==RequestType.Friend

    @property
    def isGroupReq(self) -> bool:
        return self.rtype==RequestType.Group

    @property
    def isGroupAdd(self) -> bool:
        return self.subtype=="add"
    
    @property
    def isGroupInvite(self) -> bool:
        return self.subtype=="invite"

    def addQuickReply(self,approve=True,response:str=None):
        super().addQuickReply()
        if response:
            self.response=response
        self.approve=approve

    @property
    def replyJson(self) -> dict:
        if self.quickReply:
            param={}
            param["approve"]=self.approve
            if self.response:
                if not self.approve and self.isGroupReq:
                    param["reason"]=self.response # 拒绝理由
                elif self.approve and self.isFriendReq:
                    param["remark"]=self.response # 好友备注
            return param
        return {}
    
    @property
    def sendParam(self):
        param=self.replyJson
        param["flag"]=self.flag
        if self.isGroupReq:
            param["sub_type"]=self.subtype
        return param

class Notice(BaseData):
    """ 提醒 """
    pass
