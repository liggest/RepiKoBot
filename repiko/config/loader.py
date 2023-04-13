from __future__ import annotations

import typing

from repiko.core.log import logger
if typing.TYPE_CHECKING:
    from repiko.config.config import Config
    from repiko.core.bot import Bot

class Loader:
    _subs:dict[str,type[Loader]]={}
    default:type[Loader]=None

    exts:tuple[str]=()

    def __init_subclass__(subcls):
        def gen():
            for ext in subcls.exts:
                ext=subcls.asExt(ext)
                yield ext
                subcls._subs[ext]=subcls # 顺便记录 _subs
        subcls.exts=tuple(gen())
    
    @staticmethod
    def asExt(ext:str):
        if not ext.startswith("."): # "yaml", "yml" ...
            ext=f".{ext}" # 统一 ext 为 .xxx 形式
        return ext.lower()

    @classmethod
    def get(cls,ext:str=None):
        if not ext:
            return cls.default # 用 default 设定默认 Loader
        ext=cls.asExt(ext)
        return cls._subs.get(ext) or cls.default

    @classmethod
    def save(cls,config:Config,bot:Bot=None):
        if not config.data:
            logger.warning(f"无数据，不会保存至配置 {config.pathKey} ")
            return

    @classmethod
    def load(cls,config:Config) -> dict :
        return {}

class YamlLoader(Loader):

    # import yaml
    from ruamel.yaml import YAML, Representer

    exts=(".yaml", ".yml")
    _yaml=YAML()
    _yaml.default_flow_style = False
    # _yaml.indent=4
    representer:Representer=_yaml.representer
    representer.add_multi_representer(dict, representer.__class__.represent_dict) # 支持 dict 的子类存成 dict
    # 这样就不需要下面那个修饰 ConfigMeta.__new__ 了，看起来怪怪的

    from typing import _TypedDictMeta
    def representEmptyDict(self:Representer,_):
        return self.represent_dict({})
    representer.add_representer(_TypedDictMeta, representEmptyDict) # TypedDict 的子类存成 {}

    # from repiko.config.dictsub import ConfigDict
    # representer.add_multi_representer(ConfigDict, representer.__class__.represent_dict)


    @classmethod
    def save(cls,config:Config,bot:Bot=None):
        super().save(config)
        config.path.touch()  # 见 TomlLoader
        with config.path.open("r+",encoding="utf-8") as f:
            # yaml.safe_dump(config.data,f,allow_unicode=True,sort_keys=False)
            cls._yaml.dump(config.data,f)
            f.write("\n\n")
            f.writelines( f"# {l}\n" if l else "\n" for l in config._docsGen(bot) ) # 空行前面不加 #
            f.truncate()

    @classmethod
    def load(cls,config:Config) -> dict :
        return cls._yaml.load(config.path) or super().load(config)
        # with config.path.open(encoding="utf-8") as f:
        #     return yaml.safe_load(f)

    # def decoNew(newFunc:Callable[...,type],yaml:YAML):
    #     from ruamel.yaml import Representer
    #     @classmethod
    #     def to_yaml(cls, representer:Representer, node):
    #         return representer.represent_dict(node)

    #     @functools.wraps(newFunc)
    #     def __new__(meta,name:str,bases:tuple,members:dict[str,Any],**kw):
    #         members[to_yaml.__name__]=to_yaml
    #         cls=newFunc(meta,name,bases,members,**kw)
    #         yaml.register_class(cls)
    #         logger.debug(f"registered {cls}")
    #         return cls
    #     return __new__

    # ConfigMeta.__new__=decoNew(ConfigMeta.__new__, _yaml)

import json

class JsonLoader(Loader):

    exts=(".json",)

    @classmethod
    def save(cls,config:Config,bot:Bot=None):
        super().save(config)
        config.path.touch()  # 见 TomlLoader
        with config.path.open("r+",encoding="utf-8") as f:
            json.dump(config.data,f,ensure_ascii=False,indent=4)
            f.truncate()

    @classmethod
    def load(cls,config:Config) -> dict :
        with config.path.open(encoding="utf-8") as f:
            return json.load(f) or super().load(config)

import tomli
import tomli_w

class TomlLoader(Loader):

    exts=(".toml",)

    @classmethod
    def save(cls,config:Config,bot:Bot=None):
        super().save(config)
        config.path.touch()  # 0o666
        # 用 r+ 模式打开文件，写完之后再 truncate，这样写的时候报错了应该不会把已有的内容消除
        with config.path.open("r+b") as f:
            tomli_w.dump(config.data, f)
            f.write(b"\n\n")
            f.writelines( (f"# {l}\n" if l else "\n").encode() for l in config._docsGen(bot) ) # utf-8 bytes 形式
            f.truncate()  # 只保留当前写入的内容

    @classmethod
    def load(cls,config:Config) -> dict :
        with config.path.open("rb") as f:
            return tomli.load(f) or super().load(config)

Loader.default = TomlLoader # 默认用 toml 的
