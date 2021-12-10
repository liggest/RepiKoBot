
from __future__ import annotations # 让类中定义的方法的返回值标注可以为类本身

from collections.abc import Iterable
from repiko.msg.meta import MessageMeta
from repiko.msg.util import CQescape,CQescapeComma,dealFile

class MessagePart(dict,metaclass=MessageMeta):
    """ 消息片段基类 """

    _subs:dict={}
    _data:tuple=() # 消息片段子类中定义的各参数名称

    partType:str="base"

    def __new__(cls, *args, **kw):
        if args and isinstance(args[0],dict):
            if cls is MessagePart:
                # MessagePart({"type":"text"}) 得到的是子类 Text 的对象
                subcls=cls.asPartClass(args[0])
                return super().__new__(subcls,*args,**kw)
        return super().__new__(cls,*args, **kw)

    def __init__(self,*args,**kw):
        """ 消息片段 """
        self._dictInit=bool(args) and not isinstance(args[0],str) and isinstance(args[0],Iterable) 
        # 对象是否从字典/列表/元祖等可迭代对象中创建（字符串除外）
        if self._dictInit:
            super().__init__(args[0],**kw)
        else:
            super().__init__()   # 初始化空字典
        if not "type" in self:
            self["type"]=self.partType
        if self.get("data") is None: # 防止 data 为 None
            if self._dictInit:
                self["data"]={}
            else:
                self["data"]=dict(**kw) # 不从字典中创建对象，则 kw 作为 data 里的键值对

    def __str__(self) -> str:
        return self.CQcode

    def __repr__(self) -> str: 
        # MessagePart(data1,data2,...)
        data=""
        if self.data:
            data=','.join(f"{k}={repr(v)}" for k,v in self.data.items())
        return f"{self.__class__.__name__}({data})"

    def __bool__(self): # 在 data 为空时便返回 False
        return bool(self.data)

    @classmethod
    def __init_subclass__(subcls):
        # 创建子类时，记录子类对应的消息片段类型及其本身
        subcls._subs[subcls.partType]=subcls
        super().__init_subclass__()
    
    @classmethod
    def asPartClass(cls,part:dict) -> type:
        """ 根据 part 的 type 字段寻找子类 """
        if "type" in part:
            return cls._subs.get(part["type"],cls)
        return cls
    
    @staticmethod
    def asPart(part) -> MessagePart:
        """ 将 part 转换为子类对象 """
        if type(part) in (MessagePart,dict):
            return MessagePart(part) # 得到某个 MessagePart 子类
        if isinstance(part,MessagePart): # 已经是某个 MessagePart 子类
            return part
        if isinstance(part,str):
            return Text(part)
        raise ValueError(f"无法将 {repr(part)} 转换为 MessagePart")

    @staticmethod
    def isPart(part):
        """ 判断 part 是否可转成消息片段 """
        return isinstance(part,str) or isinstance(part,dict)

    @classmethod
    def fromCQcode(cls,CQcode:str) -> MessagePart:
        CQcode=CQcode.lstrip("[").rstrip("]")
        partType,*partData=CQcode.split(",")
        if partType.startswith("CQ:"):
            partType=partType[3:]
        part={}
        part["type"]=partType
        part["data"]={}
        for d in partData:
            key,val=d.split("=",maxsplit=1)
            part["data"][key]=val
        return MessagePart(part)

    @property
    def type(self):
        """ self["type"] 消息片段类型 """
        return self["type"]

    @property
    def data(self) -> dict:
        """ self["data"] 消息片段参数 """
        return self["data"]

    @data.deleter
    def data(self):
        self["data"]=None # data置为None，后面再做把data当成字典的操作会报错
    
    @property
    def CQcode(self):
        """ 消息片段的CQ码 """
        if self.data:
            data=",".join([f"{name}={CQescapeComma(str(val))}" for name,val in self.data.items() if not val is None ])
            if data:
                return f"[CQ:{self.type},{data}]"    
        return f"[CQ:{self.type}]"

    @property
    def brief(self):
        """ 简短文本 """
        return self.CQcode

    def copy(self) -> MessagePart:
        """ 浅拷贝，但额外拷贝 data """
        obj=self.__class__(super().copy())
        obj["data"]=self.data.copy()
        return obj


class Text(MessagePart):
    """ 文本 """
    partType="text"

    text:str   # 像这样写好字段名和类型标注，自动创建对应到 self["data"][字段名] 的属性
    """ 纯文本内容 """

    def __init__(self,*texts:str,**kw):
        super().__init__(*texts,**kw)
        if not self._dictInit:          # 不从字典创建
            self.text="\n".join(texts)

    def __repr__(self) -> str: 
        # Text("...")
        return f"{self.__class__.__name__}({repr(self.text)})"

    @property
    def CQcode(self):
        return CQescape(self.text) # 纯文本没有CQ码，并且不需要转义 ","

class Face(MessagePart):
    """ 表情 """
    partType="face"

    id:str
    """ 表情ID """

    def __init__(self,id:str,**kw):
        super().__init__(id,**kw)
        if not self._dictInit:
            self.id=str(id)

    def __repr__(self) -> str: 
        # Face(123)
        return f"{self.__class__.__name__}({self.id})"

class At(MessagePart):
    """ @ """
    partType="at"

    qq:str
    """ QQ号 / 'all' """
    name:str
    """ 群内找不到QQ号时生效的名称 """

    def __init__(self,qq:str,name:str=None,**kw):
        super().__init__(qq,name,**kw)
        if not self._dictInit:
            self.qq=str(qq)
            if name:
                self.name=name

class Share(MessagePart):
    """ 链接分享 """
    partType="share"

    url:str
    """ url """
    title:str
    """ 标题 """
    content:str
    """ 内容描述 """
    image:str
    """ 图片 url """

    def __init__(self,url:str,title:str="",content:str=None,imageUrl:str=None,**kw):
        super().__init__(url,title,content,imageUrl,**kw)
        if not self._dictInit:
            self.url=url
            if not title:
                raise ValueError("请提供链接分享的标题")
            self.title=title
            if content:
                self.content=content
            if imageUrl:
                self.image=imageUrl
    
    @property
    def brief(self):
        return self.url

Link=Share

class Reply(MessagePart):
    """ 回复 """
    partType="reply"

    id:int
    """ 被回复消息的 id（需为当前聊天中的消息） """

    text:str
    """ 自定义回复 - 信息 """
    qq:int
    """ 自定义回复 - qq """
    time:int
    """ 自定义回复 - unix时间 """
    seq:int
    """ 自定义回复 - 起始消息序号 """

    def __init__(self,msgID:int,**kw):
        super().__init__(msgID,**kw)
        if not self._dictInit:
            self.id=int(msgID)

    @classmethod
    def custom(cls,text:str,qq:int,msgID:int=None,time:int=None,seq:int=None):
        """ 自定义回复 """
        obj:Reply=cls(0)
        obj.text=text
        obj.qq=int(qq)
        if msgID:
            obj.id=int(msgID)
        else:
            del obj.id
        if time:
            obj.time=time
        if seq:
            obj.seq=seq
        return obj

class Image(MessagePart):
    """ 图片 """
    partType="image"

    file:str
    """ 文件 """

    @property
    def imgType(self) -> str:
        """ 类型 \n\n 默认为空 \n\n 闪照 flash 秀图 show  """
        return self["data"].get("type")
    @imgType.setter
    def imgType(self,val:str):
        self["data"]["type"]=val
    @imgType.deleter
    def imgType(self):
        del self["data"]["type"]
    
    url:str
    """ url """
    cache:int
    """ 通过网络发送 - 使用已缓存文件 \n\n 0 不用 1 用 """
    c:int
    """ 通过网络发送 - 下载线程数 \n\n 2 或 3 """
    id:int
    """ 秀图特效 id """

    def __init__(self,file,type:str=None,cache:bool=None,**kw):
        super().__init__(file,type,cache,**kw)
        if not self._dictInit:
            self.file=dealFile(file)
            if type:
                self.imgType=type
            if not cache is None:
                self.cache=int(cache)   # False => 0  True => 1

    @classmethod
    def show(cls,file,id:int=None,cache:bool=None):
        """ 秀图 """
        obj:Image=cls(file,"show",cache)
        if id:
            obj.id=id
        return obj

    @property
    def brief(self):
        return "[图片]"

class Record(MessagePart):
    """ 语音 """
    partType="record"

    file:str
    """ 文件 """
    magic:int
    """ 是否变声 \n\n 0 不变 1 变 """
    url:str
    """ url """
    cache:int
    """ 通过网络发送 - 使用已缓存文件 \n\n 0 不用 1 用 """
    proxy:int
    """ 通过网络发送 - 使用代理下载 \n\n 0 不用 1 用 """
    timeout:int
    """ 通过网络发送 - 下载超时 """

    def __init__(self,file,magic:bool=None,cache:bool=None,proxy:bool=None,timeout:int=None,**kw):
        super().__init__(file,magic,cache,proxy,timeout,**kw)
        if not self._dictInit:
            self.file=dealFile(file)
            if not magic is None:
                self.magic=int(magic) # False => 0  True => 1
            if not cache is None:
                self.cache=int(cache)
            if not proxy is None:
                self.proxy=int(proxy)
            if not timeout is None:
                self.timeout=timeout
    
    @property
    def brief(self):
        return "[语音]"

class Video(MessagePart):
    """ 短视频 """
    partType="video"

    file:str
    """ 文件 """
    cover:str
    """ 封面 \n\n 需为 jpg """
    c:int
    """ 通过网络发送 - 下载线程数 \n\n 2 或 3 """

    def __init__(self,file,cover=None,**kw):
        super().__init__(file,cover,**kw)
        if not self._dictInit:
            self.file=dealFile(file)
            if cover:
                self.cover=dealFile(cover)

    @property
    def brief(self):
        return "[视频]"

class Forward(MessagePart):
    """ 合并转发 """
    partType="forward"

    id:str
    """ 合并转发 id """

    def __init__(self,id:str,**kw):
        super().__init__(id,**kw)
        if not self._dictInit:
            self.id=str(id)

    @property
    def brief(self):
        return "[合并转发]"

class Music(MessagePart):
    """ 音乐分享（发送） """
    partType="music"

    @property
    def musicType(self) -> str:
        """ qq、163、xm """
        return self["data"].get("type")
    @musicType.setter
    def musicType(self,val:str):
        self["data"]["type"]=val
    @musicType.deleter
    def musicType(self):
        del self["data"]["type"]
    
    id:str
    """ 歌曲 id """
    
    url:str
    """ 自定义分享 - 跳转 url """
    audio:str
    """ 自定义分享 - 音乐 url """
    title:str
    """ 自定义分享 - 标题 """
    content:str
    """ 自定义分享 - 内容描述 """
    image:str
    """ 自定义分享 - 图片 url """


    def __init__(self,id:str,src:str="qq",**kw):
        super().__init__(id,src,**kw)
        if not self._dictInit:
            self.id=str(id)
            self.musicType=src

    @classmethod
    def custom(cls,audioUrl:str,title:str,clickUrl:str,content:str=None,imageUrl:str=None):
        """ 自定义音乐分享 """
        obj:Music=cls(0,src="custom") # 自定义分享
        del obj.id
        obj.audio=audioUrl
        obj.title=title
        obj.url=clickUrl
        if content:
            obj.content=content
        if imageUrl:
            obj.image=imageUrl
        return obj

    @property
    def brief(self):
        return "[音乐]"

class Poke(MessagePart):
    """ 戳一戳（发送） """
    partType="poke"

    qq:int
    """ 待戳人 """

    def __init__(self,qq:int,**kw):
        super().__init__(qq,**kw)
        if not self._dictInit:
            self.qq=int(qq)

class TTS(MessagePart):
    """ 文本转语音 """
    partType="tts"

    text:str

    def __init__(self,text:str,**kw):
        super().__init__(text,**kw)
        if not self._dictInit:
            self.text=text

# if __name__ == "__main__":
    
#     face1={
#         "type":"face",
#         "data":{
#             "id":"123"
#         }
#     }
#     face2={
#         "type":"face",
#         "data":{
#             "id":"146"
#         }
#     }
#     text1={
#         "type":"text",
#         "data":{
#             "text":"真巧，你也网上冲浪啊"
#         }
#     }
#     text2={
#         "type":"text",
#         "data":{
#             "text":"你是GG还是MM"
#         }
#     }
    


