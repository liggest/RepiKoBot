from __future__ import annotations

import inspect
from pathlib import Path
# from collections import UserDict

from typing import Any, Callable, TYPE_CHECKING, TypeVar

from repiko.core.log import logger
from repiko.core.constant import EventNames
from repiko.config.meta import ConfigMeta
from repiko.config.loader import Loader
from repiko.config.defaults import DefaultsPattern
from repiko.config.util import eventDocsGen
if TYPE_CHECKING:
    from repiko.core.bot import Bot

from LSparser import Events

T=TypeVar("T")

class Config:
    
    baseDir=Path("config")

    _configs:dict[str,Config]={}

    @classmethod
    def defaultBase(cls,name:Path):
        if name.parts and name.parts[0]==cls.baseDir.name: # 以 config/... 开头的路径
            return name
        if name.is_absolute():
            parent=name.parent
            if parent.is_dir(): # 绝对路径且目录存在
                return name
            name=name.name # 文件名
            logger.warning(f"用于放置配置 {name} 的目录 {parent.as_posix()} 不存在，尝试在 {cls.baseDir.as_posix()} 下寻找 {name}")
        return cls.baseDir / name # config/name

    @classmethod
    def defaultName(cls,withParent=True):
        """  调用 Config 的模块的名字  """
        frame=inspect.currentframe()
        while frame:
            code=frame.f_code
            if code.co_name=="<module>": # 首个模块级的调用
                path=Path(code.co_filename)
                name=path.stem # 模块的文件名（不带后缀）
                if withParent and path.parent.name:
                    name=f"{path.parent.name}/{name}" # 试着加上一层 parent 的名字
                return name
            frame=frame.f_back

    @classmethod
    def asName(cls,name:Path|str=None):
        if name is None:
            name=cls.defaultName()
        if not isinstance(name,Path):
            name=Path(name)
        return name

    @classmethod
    def _pathGen(cls, name:Path, exts:tuple[str]=None):
        if not name.suffix and exts:
            for ext in exts:
                yield cls.defaultBase(name.with_suffix(ext))
        else:
            yield cls.defaultBase(name)

    @classmethod
    def locateFile(cls,name:Path,exts:tuple[str]=None) -> Path:
        first=None
        for path in cls._pathGen(name,exts):
            if path.is_file():
                return path # 优先用存在的路径
            if not first:
                first=path
        return first  # 否则用第一个路径

    @staticmethod
    def path2key(path:Path):
        return path.as_posix()

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self,val:Path):
        self._path=val
        self._pathkey=None # 重置 pathKey

    @property
    def name(self):
        return self._name.as_posix() if isinstance(self._name,Path) else self._name

    @property
    def data(self):
        return self._data

    @property
    def pathKey(self):
        if not self._pathkey:
            self._pathkey=self.path2key(self.path)
        return self._pathkey
    
    @property
    def initEventName(self):
        return EventNames.ConfigInit(self.pathKey)

    @property
    def updateEventName(self):
        return EventNames.ConfigUpdate(self.pathKey)

    def __new__(cls,name:str|Path=None):
        pname=cls.asName(name)
        if name is None:
            name=pname.as_posix() # 展示用
        loader=Loader.get(pname.suffix)
        path=cls.locateFile(pname,loader.exts)

        obj=cls._configs.get(cls.path2key(path))
        if not obj:
            obj=super().__new__(cls)  # 没有的话就 new 一个
            obj._setMembers(path,name,loader)
        return obj

    def _setMembers(self,path:Path, name:str|Path|None, loader:type[Loader]):
        self.path=path
        self._name=name
        self._loader=loader

        self._data:dict=None
        self._pattern=None
        self._patternAccepter=None
        self._defaultsFrame=None

    # def __init__(self,name:str|Path=None):

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self._name)})"

    def _ensureStore(self):
        """  确保 self 在 Config._configs 中  """
        if self.pathKey not in self._configs:
            self._configs[self.pathKey]=self

    def _pattern2data(self):
        accepter=self._patternAccepter or DefaultsPattern.get(self._pattern)
        if accepter:
            self._patternAccepter=accepter
            return accepter.toData(self)
        return {}
        # if not self._pattern:
        #     self._data={}
        # elif isinstance(self._pattern,ConfigMeta):
        #     self._data=self._pattern({})
        # elif isinstance(self._pattern,dict):
        #     self._data=self._pattern
        # elif is_typeddict(self._pattern):
        #     pattern:type[TypedDict]=self._pattern
        #     anno:dict[str,str|type]=getattr(pattern,"__annotations__",{})
        #     self._data={ k:getattr(pattern,k,None) for k in anno }

    @property
    def _defaultsLocal(self):
        if self._defaultsFrame:
            return dict(self._defaultsFrame.f_locals)
        return None

    def onInit(self,func:Callable[[Any,Bot],bool]):
        """  
            `func(data:Any, bot:Bot) -> bool`\n
            data 的类型为 Config.defaults 传入的类（或者 dict）\n
            返回值为 True 时立即保存配置
        """
        self._ensureStore()
        return Events.on(self.initEventName)(func)

    def onUpdate(self,func:Callable[[Any,Bot],bool]):
        """  
            `func(data:Any, bot:Bot) -> bool`\n
            data 的类型为 Config.defaults 传入的类（或者 dict）\n
            返回值为 True 时立即保存配置
        """
        self._ensureStore()
        return Events.on(self.updateEventName)(func)

    def on(self,func:Callable[[Any,Bot],bool]):
        """  
            `func(data:Any, bot:Bot) -> bool`\n
            相当于 func 同时传入 onInit 和 onUpdate
        """
        self._ensureStore()
        func=Events.on(self.initEventName)(func)
        return Events.on(self.updateEventName)(func)

    def _initData(self,bot:Bot=None):
        self._data=self._pattern2data()
        if not self.path.is_file(): # 文件不存在
            logger.warning(f"配置 {self.pathKey} 不存在，尝试根据默认配置创建…")
            if not self.path.is_absolute() and not self.path.parent.exists(): # 不是绝对路径的话，把目录也创出来
                self.path.parent.mkdir(parents=True)
            self.save(bot)
        else:
            logger.info(f"加载配置 {self.pathKey} …")
            self.load()

    def _init(self,bot:Bot=None):
        self._initData(bot)
        return bot and any(bot.EM.send(self.initEventName,self.data,bot=bot)) # bot 为 None 时返回 None

    async def _asyncInit(self,bot:Bot=None):
        self._initData(bot)
        return bot and any(await bot.EM.asyncSend(self.initEventName,self.data,bot=bot))

    def init(self,bot:Bot=None):
        if self._init(bot): # 返回 True 时保存配置
            self.save(bot)
        return self.data
    
    async def asyncInit(self,bot:Bot=None):
        if await self._asyncInit(bot): # 返回 True 时保存配置
            self.save(bot)
        return self.data

    def _update(self,bot:Bot=None):
        logger.info(f"更新配置 {self.name} …")
        return bot and any(bot.EM.send(self.updateEventName,self.data,bot=bot))

    async def _asyncUpdate(self,bot:Bot=None):
        logger.info(f"更新配置 {self.name} …")
        return bot and any(await bot.EM.asyncSend(self.updateEventName,self.data,bot=bot))

    def update(self,bot:Bot=None):
        if self._update(bot): # 返回 True 时保存配置
            self.save(bot)
        return self.data

    async def asyncUpdate(self,bot:Bot=None):
        if await self._asyncUpdate(bot): # 返回 True 时保存配置
            self.save(bot)
        return self.data

    def initUpdate(self,bot:Bot=None):
        rinit=self._init(bot)
        rupdate=self._update(bot)
        if rinit or rupdate: # 返回 True 时保存配置
            self.save(bot)
        return self.data
    
    async def asyncInitUpdate(self,bot:Bot=None):
        rinit=await self._asyncInit(bot)
        rupdate=await self._asyncUpdate(bot)
        if rinit or rupdate: # 返回 True 时保存配置
            self.save(bot)
        return self.data

    def defaults(self,pattern:T) -> T:
        """
            设定配置的默认样式，目前支持
            - 传入字典对象提供默认值
            - 传入 typing.TypedDict 提供配置结构与默认值
            - 传入自定义类型，提供配置结构与默认值（可嵌套）

            （一个配置仅能传入一个样式）

            ```python
                @Config(...).defaults
                class MyConfig:
                    x = 1
                    y = ["a", "b", "c"]
                    z:str

                    class Nested:
                        n1:str = "name"
                        n2:int = 3

            ```
        """
        self._ensureStore()
        accepter=DefaultsPattern.get(pattern)
        if accepter:
            self._patternAccepter=accepter
            self._defaultsFrame=inspect.currentframe().f_back
            return accepter.accept(self,pattern)
        
        logger.warning(f"无法让配置 {self.name} 拥有默认样式 {repr(pattern)}!")
        return pattern
        # if isinstance(pattern,dict) or is_typeddict(pattern): # 传入字典 或传入 TypedDict（装饰器）
        #     self._pattern=pattern
        #     return pattern
        # if isinstance(pattern,type): # 传入类（装饰器）
        #     self._pattern=ConfigMeta(pattern.__name__, (pattern,*pattern.__bases__), pattern.__dict__)
        #     return self._pattern # 返回新类

    __call__=defaults

    def withDefaults(self,pattern:T):
        """  同 Config(...).defaults，但返回 Config 本身  """
        pattern=self.defaults(pattern)
        if self._patternAccepter:
            self._defaultsFrame=inspect.currentframe().f_back # 再外层
            if hasattr(pattern,"__name__"):
                self._defaultsFrame.f_locals[pattern.__name__] = pattern
        return self

    @staticmethod
    def considerClass(cls:type):
        """  装饰自定义类 cls，使其对象在程序与配置文件中作为 dict 使用  """
        return ConfigMeta.mimic(cls)

    def _docsGen(self,bot:Bot):
        if self._patternAccepter:
            yield from self._patternAccepter.docsGen(self)
        yield ""  # 空行
        yield from eventDocsGen(self.initEventName,bot,title="初始化时")
        yield from eventDocsGen(self.updateEventName,bot,title="更新时")

    # def docs(self,bot:Bot):
    #     return "\n".join(self._docsGen(bot))

    def load(self):
        data=self._loader.load(self)
        if self._patternAccepter:
            self._data=self._patternAccepter.updateData(self,data)
        else:
            self._data=data

    def save(self,bot:Bot=None):
        logger.info(f"保存配置 {self.pathKey} …")
        self._loader.save(self,bot)

    from repiko.config.meta import Unit # Config.Unit ...
