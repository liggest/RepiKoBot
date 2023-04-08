from __future__ import annotations

from typing import TYPE_CHECKING, Generator #, TypedDict, is_typeddict, 

from repiko.config.pattern import TypeHelper, Pattern
if TYPE_CHECKING:
    from repiko.config.config import Config

class DefaultsPattern:
    
    _subs:list[type[DefaultsPattern]] = []

    def __init_subclass__(subcls):
        subcls._subs.append(subcls) # 记录 _subs

    @classmethod
    def get(cls, pattern):
        if any(subcls := s for s in cls._subs if s.canAccept(pattern)):
            return subcls

    @classmethod
    def canAccept(cls, pattern):
        return pattern is None

    @classmethod
    def accept(cls, config:Config, pattern:None):
        pass

    @classmethod
    def toData(cls, config:Config) -> dict:
        return {}

    @classmethod
    def updateData(cls, config:Config, data:dict):
        if config._data:
            config._data.update(data)
            return config._data
        return data
    
    @classmethod
    def docsGen(cls, config:Config) -> Generator[str, None, None]:
        return
        yield
        
        

class DictPattern(DefaultsPattern):

    @classmethod
    def canAccept(cls, pattern):
        return isinstance(pattern,dict)

    @classmethod
    def accept(cls, config:Config, pattern:dict):
        config._pattern = pattern
        return pattern

    @classmethod
    def toData(cls, config:Config) -> dict:
        return { **config._pattern } # 只是浅拷贝，需要注意

# class TypedDictPattern(DefaultsPattern):

#     # _defaults:dict[type[TypedDict],dict]=None

#     @classmethod
#     def canAccept(cls,pattern):
#         return is_typeddict(pattern)

#     @classmethod
#     def accept(cls, config:Config, pattern:type[TypedDict]):
#         config._pattern = Pattern.mimic(pattern)
#         return config._pattern

#     @classmethod
#     def toData(cls, config:Config) -> dict:
#         # return cls._toData(config._pattern,extraLocals)
#         # return ConfigDict(pattern=config._pattern, patternLocal=config._defaultsLocal)._defaults
#         return Pattern.mimic(config._pattern)._defaults

#     # @classmethod
#     # def _toData(cls,pattern:type[TypedDict],extraLocals:dict=None):
#     #     anno=getClsAnnotations(pattern,extraLocals)

#     #     def lazyTypedDict(self:LazyDict,key:str,val):
#     #         if val is None or (not isinstance(val,LazyDict) and val=={}):
#     #             if (tp:=anno.get(key)):
#     #                 val=_handleType(tp)
#     #                 super(self.__class__,self).__setitem__(key,val)
#     #         return val

#     #     # def lazyTypedDict(self:LazyDict,key:str,val):
#     #     #     if is_typeddict(val): # key 取出来的值是 TypedDict 的话，处理之，得到的 LazyDict 存入 key
#     #     #         logger.debug(handled)
#     #     #         if handled and val in handled: # 处理过的可以直接用
#     #     #             val=handled[val]
#     #     #         else:
#     #     #             val=cls._toData(val)
#     #     #         super(self.__class__,self).__setitem__(key,val)
#     #     #     return val

#     #     cls._defaults[pattern]=None
#     #     # data=LazyDict(cls._toDataGen(pattern)).withCallback(lazyTypedDict)
#     #     data=LazyDict( (k,cls._handleType(v)) for k,v in anno.items() ).withCallback(lazyTypedDict)
#     #     cls._defaults[pattern]=data
#     #     return data

#     # @classmethod
#     # def _toDataGen(cls,pattern:type[TypedDict]):
#     #     anno=getClsAnnotations(pattern)
#     #     yield from ( (k,cls._handleType(v)) for k,v in anno.items())
#     #     # for k,v in anno.items():
#     #     #     if is_typeddict(v):
#     #     #         yield k, dict(cls._toDataGen(v))
#     #     #     else:
#     #     #         yield k, cls._handleType(v)

#     # @classmethod
#     # def _handleType(cls,v):
#     #     if is_typeddict(v):
#     #         # if cls._defaults is None:
#     #         #     cls._defaults={}
#     #         if v in cls._defaults: # v 处理过了，只处理一次
#     #             return {}
#     #         else:
#     #             return cls._toData(v) # v 还没处理过，处理一次
#     #     origin, args=get_origin(v), get_args(v) # Literal[3] => Literal  (3,)
#     #     if origin is Literal and args:
#     #         if len(args)==1:
#     #             return args[0]
#     #         else: 
#     #             return args   # 如果长度不为 1，以元组形式返回
#     #     elif (origin is Union or origin is UnionType) and args:
#     #         return cls._handleType(args[0]) # Union 中的第一项
#     #     elif isinstance(v,type) or callable(v): # callable 范围太广了...
#     #         return v()
#     #     return v

#     @classmethod
#     def updateData(cls, config:Config, data:dict):
#         # return cls._fromData(data,config._pattern)
#         # return ConfigDict(data, pattern=config._pattern, patternLocal=config._defaultsLocal)
#         return Pattern.mimic(config._pattern)._defaultsNoOptionals._updateWith(data)

#     # @classmethod
#     # def _fromData(cls,data:dict,pattern:type[TypedDict]):
#     #     anno=getClsAnnotations(pattern)
#     #     if cls._defaults is None:
#     #         cls._defaults={}
            
#     #     def lazyTypedDict(self:LazyDict,key:str,val):
#     #         if (tp:=anno.get(key)) and is_typeddict(tp):
#     #             if val is None:
#     #                 val=cls._toData(tp)
#     #             elif not isinstance(val,LazyDict) and isinstance(val,Mapping):
#     #                 val=cls._fromData(val,tp)
#     #             super(self.__class__,self).__setitem__(key,val)
#     #         return val
        
#     #     return LazyDict(data).withCallback(lazyTypedDict)        

#     @classmethod
#     def docsGen(cls, config:Config):
#         # if isinstance(config.data,Pattern):
#         #     return config.data._docsGen()
#         # return ConfigDict(pattern=config._pattern, patternLocal=config._defaultsLocal)._docsGen()
#         return Pattern.mimic(config._pattern)._docsGen()

# class UnitPattern(DefaultsPattern):

#     @classmethod
#     def canAccept(cls,pattern):
#         return isinstance(pattern,type) and issubclass(pattern,UnitDict) # pattern 是 UnitDict 子类
    
#     @classmethod
#     def accept(cls,config:Config,pattern:type[UnitDict]):
#         config._pattern=pattern
#         return pattern
    
#     @staticmethod
#     def _toData(config:Config) -> UnitDict:
#         return config._pattern()

#     @classmethod
#     def toData(cls,config:Config) -> dict:
#         return cls._toData(config)._defaults

#     @classmethod
#     def updateData(cls,config:Config,data:dict):
#         return config._pattern(data)

#     @classmethod
#     def docsGen(cls,config:Config):
#         if isinstance(config.data,UnitDict):
#             return config.data._docsGen()
#         return cls._toData(config)._docsGen()

class ClassPattern(DefaultsPattern):

    @classmethod
    def canAccept(cls, pattern):
        return isinstance(pattern,type) and not TypeHelper.isBuiltin(pattern)  # pattern 是类，也包含了 TypedDict

    @classmethod
    def accept(cls, config:Config, pattern:type):
        config._pattern = Pattern.mimic(pattern, config._defaultsFrame)  # 用 Pattern 包装，Pattern、pattern 作为基类
        return config._pattern

    @classmethod
    def toData(cls, config:Config) -> dict:
        return Pattern.mimic(config._pattern)._defaults

    @classmethod
    def updateData(cls, config:Config, data:dict):
        return Pattern.mimic(config._pattern)._defaultsNoOptionals._deepUpdateWith(data)

    @classmethod
    def docsGen(cls, config:Config):
        return Pattern.mimic(config._pattern)._docsGen()

DefaultsPattern._subs.append(DefaultsPattern)  # 最后处理 pattern=None 的情况
    



