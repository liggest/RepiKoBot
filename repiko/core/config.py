
from __future__ import annotations
from pathlib import Path
from typing import Callable,Dict,List,Union,TYPE_CHECKING
from LSparser import Events

from repiko.core.constant import EventNames

import yaml
import traceback

if TYPE_CHECKING:
    from repiko.core.bot import Bot

class Config:
    
    baseDir=Path("config")

    _configs:Dict[str,Config]={}
    _unloaded:Dict[str,Config]={}
    _errors:List[Exception]=[]

    @staticmethod
    def defaultName():
        return Path("config.yaml")

    @classmethod
    def defaultPath(cls,name):
        return cls.baseDir / name

    @staticmethod
    def asKey(path:Path):
        return path.as_posix()

    @classmethod
    def fileName(cls,name:Path,ext=".yaml"):
        if not ext.startswith("."):
            ext=f".{ext}"
        return name.with_suffix(ext)

    @classmethod
    def findFile(cls,name:Path):
        path=cls.defaultPath(name)
        if path.is_file():
            return path
        elif name.is_file():
            return name

    def __new__(cls,name:Union[str,Path]=None):
        if name is None:
            name=cls.defaultName()
        if not isinstance(name,Path):
            name=Path(name)

        path=None
        if name.suffix in (".yaml",".yml"):
            path=cls.findFile(name)
        else:
            name=cls.fileName(name,".yml") # xxx.yml
            path=cls.findFile(name)
            if path is None:
                name=cls.fileName(name) # xxx.yaml 这样没有文件时默认创建 xxx.yaml
                path=cls.findFile(name)

        if path is None: # 没找到文件
            if len(name.parts)<2: # 只有一层 xxx/yyy.yaml
                path=cls.defaultPath(name)
            else:
                path=name # 两层以上 xxx/yyy.yaml
        if path.is_absolute():
            try:
                path=path.relative_to(Path.cwd())
            except:
                path=path
        obj=cls._configs.get(cls.asKey(path),super().__new__(cls)) # 没有的话就 new 一个
        obj.path=path
        print(path,name)
        return obj

    def __init__(self,name:Union[str,Path]=None):
        """
            加载配置 name 时
            ```
            @Config(name)
            def onConfig(config: dict | list ,bot:Bot):
                pass
            ```
        """
        self.content=None
        if not hasattr(self,"path"):
            self.path=self.defaultPath(self.defaultName())

    def __repr__(self):
        s=[f"{type(self).__name__}({repr(self.path)}"]
        if self.content is not None:
            s.append(f",{repr(self.content)}")
        s.append(")")
        return "".join(s)

    @property
    def pathKey(self):
        return self.asKey(self.path)

    @property
    def eventName(self):
        return EventNames.Config(self.pathKey)

    def ensure(self):
        if self.pathKey not in self._configs:
            self._configs[self.pathKey]=self

    def on(self,func:Callable[[Union[dict,list],Bot],None]):
        self.ensure()

        if self.content is None:
            self._unloaded[self.pathKey]=self
        
        Events.on(self.eventName)(func)

    __call__=on

    def load(self):
        content=None
        if self.path.exists():
            with open(self.path,encoding="utf-8") as f:
                content=yaml.safe_load(f)
            if isinstance(content,dict):
                content=ConfigDict(content)
            elif isinstance(content,(list,tuple)):
                content=list(content)
            else:
                content=[content]
            self.content=content
            print(f"加载了配置：{self.path}")
            return self.content or True

    def write(self,bot:Bot=None):
        content= dict(self.content) if isinstance(self.content,ConfigDict) else self.content
        with open(self.path,"w",encoding="utf-8") as f:
            yaml.safe_dump(content,f,allow_unicode=True,sort_keys=False)
            if bot:
                for func in bot.EM.get(self.eventName):
                    func:Callable
                    if func and hasattr(func,"__doc__") and func.__doc__: # 把回调的注释也写成配置的注释
                        f.write("\n")
                        f.writelines(f"# {line}" for line in func.__doc__.splitlines())

    def do(self,bot:Bot,load=True):
        self.ensure()

        noFile=self.content is None
        load|=self.pathKey in self._unloaded
        if noFile or load:
            noFile=not bool(self.load())
            if not noFile and self.pathKey in self._unloaded:
                self._unloaded.pop(self.pathKey)

        if noFile:
            content=ConfigDict()
            try:
                bot.EM.send(self.eventName,content,bot=bot)
            except Exception as e:
                self._errors.append(e)
            if content:
                parent=self.path.parent
                if not parent.exists():
                    parent.mkdir(755,True,True)
                self.content=content
                self.write(bot)
                self._errors.append(FileNotFoundError(f"未找到 {self.path}  已尝试生成该文件，请填写后重新运行程序"))
        else:
            try:
                bot.EM.send(self.eventName,self.content,bot=bot)
            except Exception as e:
                self._errors.append(e)
                if isinstance(self.content,ConfigDict) and self.content.changed:
                    print(f"检测到运行中配置内容变化，覆写至 {self.path}")
                    self.write(bot)
                    self.content.changed=False
        
        return self

    @classmethod
    def dumpErrors(cls):
        if cls._errors:
            for e in cls._errors[:-1]:
                traceback.print_exception(type(e),e,e.__traceback__)
            last=cls._errors[-1]
            cls._errors.clear()
            raise last
    
    @classmethod
    def loadAll(cls,bot:Bot):
        for pathKey,config in list(cls._unloaded.items()):
            config.do(bot)
        cls.dumpErrors()
        
        

class ConfigDict(dict):

    def __new__(cls, *args, **kwargs):
        obj:ConfigDict=super().__new__(cls,*args, **kwargs)
        obj._changed=False
        obj._config=None
        return obj

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self,val:Config):
        self._config=val

    @property
    def changed(self):
        return self._changed

    @changed.setter
    def changed(self,val:bool):
        self._changed=bool(val)

    def __getitem__(self, key):
        if key not in self:
            self.__setitem__(key,"") # 默认为空字符串
        return super().__getitem__(key)

    def __setitem__(self, key, val) -> None:
        self.changed=True
        return super().__setitem__(key, val)

    def __getattr__(self, name):
        try:
            return self[name]
        except:
            return super().__getattr__(name)

    def __setattr__(self, name: str, val):
        # if not name.startswith("_") and name not in dir(self):
        if not name.startswith("_") and name not in self.__dict__ and name not in type(self).__dict__:
            self.__setitem__(name,val)
        return super().__setattr__(name, val)


if __name__ == "__main__":
    from LSparser import CommandCore

    class Fake:
        pass

    bot=Fake()
    bot.EM=CommandCore.getLast().EM

    @Config("basic")
    def basic(config:dict ,bot:Bot):
        """ 基础配置 """
        c1=config["c1"]
        c2=config.c2
        c3=config["c3"]
        c4=config.setdefault("c4",4)

    @Config("extra.yml")
    def extra(config:ConfigDict ,bot:Bot):
        """ 额外配置 """
        config["e1"]
        config["e2"]
        config["e3"]
        # print("changed",config.changed)

    @Config("error.yml")
    def extra(config:ConfigDict ,bot:Bot):
        """ 错误配置 """
        import random
        config["before"]
        config["rand"]=random.randint(0,100)
        1/0
        config["after"] # 这里应该就记录不到了

    # @Config("config!.yaml")
    # def extra(config:ConfigDict ,bot:Bot):
    #     """ 已经存在的 """
    #     print("system",config["system"])
    #     print("admin",config["admin"])
    #     print(config)


    # @Config("config!.yml")
    # def extra(config:ConfigDict ,bot:Bot):
    #     """ 不存在的 """
    #     print("system",config["system"])
    #     print("admin",config["admin"])
    #     print(config)

    # @Config(Path.cwd() / "ygo.yml")
    # def basic(config:ConfigDict ,bot:Bot):
    #     """ 别的地方的 """
    #     config["y1"],config["y2"],config["y3"]
