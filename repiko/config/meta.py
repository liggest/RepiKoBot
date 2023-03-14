

import inspect
import functools
from typing import Any, Callable, Mapping, get_origin, get_args, NewType
from inspect import get_annotations
from types import FrameType

from collections import defaultdict
from itertools import chain

from repiko.core.log import logger
# from repiko.config.lazydict import LazyDict
from repiko.config.dictsub import ConfigDict, UnitDict
from repiko.config.util import looseGetattr, ClassDict, just, deAnnotated, isBuiltinType, Undefined #, get_annotations


class ConfigMeta(type):
    
    DictCls=ConfigDict

    @classmethod
    def mimic(meta,cls:type):
        """  如果 cls 没有 DictCls 基类，则用 ConfigMeta 作元类，DictCls、cls 作基类  """
        if issubclass(cls,meta.DictCls):
            return cls
        return ConfigMeta(cls.__name__, (meta.DictCls,*meta.DictCls.__bases__, cls,*cls.__bases__), dict(cls.__dict__), cls=cls)

    # @classmethod 
    # def __prepare__(meta,name:str,bases:tuple,**kw) -> dict:  # 根本没在工作
    #     members=super().__prepare__(name,bases,**kw)
    #     return members

    _classes=set()
    # _initings=set() # 正在用 setDictProperties 初始化的类

    def __new__(meta,name:str,bases:tuple,members:dict[str,Any],cls=None,**kw):
        members.pop("__dict__",None)
        members.pop("__weakref__",None)
        # cls,*_=bases
        if not cls:
            cls=bases[ len((meta.DictCls,*meta.DictCls.__bases__)) ]
        logger.debug(f"装饰 {repr(cls)} ...")
        
        # annos=meta.setAnnotations(name,members)
        annos=get_annotations(cls,eval_str=False)
        newMembers,defaults=meta.setProperties(name,members,annos)
        # newMembers=meta.setProperties(name,members,annos)
        meta.setInit(members,newMembers)
        meta.setSetattr(members,newMembers)
        meta.setRepr(members,newMembers)
        meta.setDefaults(newMembers,defaults)

        # logger.debug(members)
        newCls=super().__new__(meta,name,bases,newMembers,**kw)
        # YamlLoader._yaml.register_class(newCls)
        meta._classes.add(newCls)  # 记录自己创建的类
        setattr(cls,"__mimic__",newCls)  # 暂时让原来的类能找到代替它的类
        return newCls

    @staticmethod
    def keyProperty(key:str,anno:str|type):
        def kget(self:dict) -> anno:
            try:
                return self[key]
            except KeyError as e:
                raise AttributeError from e # 当作发出 AttributeError

        def kset(self,val:anno):
            self[key]=val
        def kdel(self):
            del self[key]
        return property(kget,kset,kdel,f"self[{repr(key)}]")

    # @staticmethod
    # def keyDictProperty(key:str,cls:type):
    #     def kget(self:dict) -> cls:
    #         try:
    #             val=self[key]
    #             if not isinstance(val,cls) and isinstance(val,Mapping):
    #                 kset(self,val)
    #                 return self[key]
    #             return val
    #         except KeyError as e:
    #             raise AttributeError from e # 当作发出 AttributeError

    #     def kset(self,val:cls): # 修改 setter，
    #         if not isinstance(val,cls) and isinstance(val,Mapping):
    #             val=cls(val)
    #             # logger.debug(f"=== kset === {repr(val)}")
    #         self[key]=val
    #     def kdel(self):
    #         del self[key]
    #     setattr(kset,"_dictProp",True) # kset 用这个这个字段来表明与 keyProperty 设置的属性不同
    #     return property(kget,kset,kdel,f"self[{repr(key)}]")

    # @classmethod
    # def setAnnotations(meta,name:str,members:dict[str,Any]) -> dict:
    #     annos=members.get("__annotations__",{})
    #     # clsModule=members.get("__module__")
    #     for k,v in annos.items():
    #         # if v==name:  # 类里成员的类型是类本身
    #         #     annos[k]=ForwardRef(k,module=clsModule,is_class=True)
    #         if k not in members:
    #             members[k]=None # 总有默认值
    #     return annos

    @classmethod
    def setProperties(meta, name:str,members:dict[str,Any], annos:dict[str,str|type]) -> tuple[dict[str,Any],dict[str,Any]]:
        defaults={}
        def membersGen(): # 过滤 members 中的项
            for k,v in annos.items():
                if k.endswith("__"): # 不管双下划线
                    continue
                if k not in members: # 只有注解的
                    yield k, meta.keyProperty(k,v) # 变成属性

            for k,v in members.items():
                if isinstance(v,type) and not inspect.isbuiltin(v) and v not in meta._classes: # 非内建类、非已装饰过的
                    if name:
                        parentName=v.__qualname__.removesuffix(v.__name__)
                        # logger.debug(parentName)
                        if parentName.endswith(".") and parentName[:-1].endswith(name): # cls 的内部类
                            yield k, ConfigMeta.mimic(v)  # 内部类都装饰一下
                    continue
                if callable(v) or isinstance(v,(classmethod,property)): # 不管可调用对象、property
                    continue
                if k.endswith("__"): # 双下划线字段原封不动
                    yield k,v
                else:
                    anno=annos.get(k,Any) # 默认注解 Any
                    defaults[k]=v
                    yield k, meta.keyProperty(k,anno) # 变成属性
        newMembers=dict(membersGen())
        return newMembers,defaults # 返回 newMembers 和收集的默认值
        # return newMembers # 返回 newMembers

    @classmethod
    # def setInit(meta, members:dict[str,Any], defaults:dict[str,Any], newMembers:dict[str,Any], cls):
    def setInit(meta, members:dict[str,Any], newMembers:dict[str,Any]):
        clsInit:Callable=members.get("__init__")
        if clsInit:
            sig=inspect.signature(clsInit)

            def __cls__init__(self:dict,*iargs,**ikw): # 试着调用类原来的 init，并尽量匹配参数
                args=[]
                kw={}
                def feedArgs(): # 优先用 iargs 填充 args
                    nonlocal iargs
                    if iargs:
                        args.append(iargs[0])
                        iargs=iargs[1:]
                        return True
                
                def feedKW(name:str,default): # 优先用 ikw 填充 kw
                    if (pval:=ikw.pop(name,default)) != default:
                        kw[name]=pval
                        return True

                afterSelf=False
                for name,param in sig.parameters.items():
                    if not afterSelf:
                        afterSelf=True
                        continue
                    if param.kind==param.POSITIONAL_ONLY: # 仅位置参数
                        if not feedArgs():
                            args.append( looseGetattr(self,name,None if param.default==param.empty else param.default) )
                    elif param.kind==param.VAR_POSITIONAL: # 有 *args
                        args.extend(iargs)
                    elif param.kind==param.VAR_KEYWORD: # 有 **kw
                        kw.update(ikw)
                    else: # 剩下的都当做关键字参数 
                        if param.kind == param.POSITIONAL_OR_KEYWORD and feedArgs(): # 可能是位置参数或关键字参数
                            continue  # 成功用 iargs 填入
                        if not feedKW(name,param.empty): # 试着用 ikw 填入
                            kw[name]=looseGetattr(self,name,None if param.default==param.empty else param.default)
                    #     if (pval:=ikw.pop(name,param.empty)) != param.empty:
                    #         kw[name]=pval
                    #     else:
                            
                
                logger.debug(f"{repr(self)}.__init__(*{repr(args)}, **{repr(kw)})")

                # code=clsInit.__code__
                # varNames=code.co_varnames[:code.co_argcount]  # (x,y,z,args,kw) ... co_argcount==3
                # posOnly=code.co_posonlyargcount
                # pos=[ looseGetattr(self,name,None) for name in varNames[:posOnly] ] # 只能是位置参数的
                # keyword={ name:looseGetattr(self,name,None) for name in varNames[posOnly:] } # 剩下的都当做关键字参数处理
                # if code.co_flags & inspect.CO_VARARGS: # 有 *args
                    
                #     pos.extend(args)
                # if code.co_flags & inspect.CO_VARKEYWORDS: # 有 **kw
                    
                #     keyword.update(kw)
                # try:
                # except TypeError as e:
                #     if e.args and "super(" in e.args[0]:
                #         raise TypeError("由于设计上的局限性，在该类的方法中使用 super 时请显式使用 super(type(self),self) 的形式") from e
                #     raise e
                clsInit(self,*args,**kw) # 调用类原来定义的 __init__

        # anno=None

        def __init__(self:dict,data=None,*args,**ikw):
            # nonlocal anno
            if not (data is None or isinstance(data,Mapping)): # data 只接收 None 和 Mapping
                args=(data,)+args # 如果 data 是别的，当做 args 中的一个处理
                data=None
            ikw.pop("pattern",None)
            patternLocal=ikw.pop("patternLocal",None)
            meta.DictCls.__init__(self, data, pattern=self.__class__, patternLocal=patternLocal)
            # dict()                                 # dict(data)
            # dict.__init__(self,data,**ikw) 
            # dict init，最多只有一个位置参数
            # if self.__class__ not in meta._initings:
            #     anno=meta.setDictProperties(self.__class__, self, anno)
            
            # if defaults:
            #     for k,v in defaults.items():    # 设置收集到的默认值
            #         self.setdefault(k,v)

            if clsInit:
                __cls__init__(self,*args,**ikw) # 试着调用类原来定义的 __init__
        
        newMembers["__init__"]=functools.wraps(clsInit)(__init__) if clsInit else __init__

    @classmethod
    def setSetattr(meta, members:dict[str,Any], newMembers:dict[str,Any]):
        clsSetattr:Callable=members.get("__setattr__")

        def __setattr__(self:dict, name:str, value:Any):
            # logger.debug(f"__setattr__ {name}")
            if not (name.endswith("__") or hasattr(self.__class__, name)): # 不管双下划线、不反复设置类的属性  
                # logger.debug(f"__set_class_attr__ {name}")
                pvalue=meta.keyProperty(name,Any)
                setattr(self.__class__,name,pvalue) # 给类设置属性
            super(type(self),self).__setattr__(name,value)
            # setattr(self,name,value)
        
        newMembers["__setattr__"]=functools.wraps(clsSetattr)(__setattr__) if clsSetattr else __setattr__

    @classmethod
    def setRepr(meta, members:dict[str,Any], newMembers:dict[str,Any]):
        clsRepr:Callable=members.get("__repr__")
        if clsRepr:
            newMembers["__repr__"]=clsRepr  # 用原来定义的 repr
        # 否则用 ConfigDict 定义的 repr
        # else:
        #     def __repr__(self:dict) -> str: # 自定义 repr
        #         return f"{self.__class__.__name__}({meta.DictCls.__repr__(self)})"
        #     newMembers["__repr__"]=functools.wraps(clsRepr)(__repr__) if clsRepr else __repr__

    @classmethod
    def setDefaults(meta, newMembers:dict[str,Any], originDefaults:dict[str,Any]):
        clsDefaults:property=ConfigDict._defaults

        @property
        @functools.wraps(clsDefaults.fget)
        def _defaults(self:ConfigDict): # getter 稍作修改
            cls=self.__pattern__
            if not cls:
                return self._emptyCopy

            # if self.defaultedSet and cls in self.defaultedSet:
            #     return self._emptyCopy

            defaults=getattr(cls,"__default_values__",None)
            if defaults is None:
                defaults=self._emptyCopy
                self._defaults=defaults # 防止递归
                # defaults=self._getDefaults()
                anno=self._anno
                optionals=set()
                if anno:
                    for k,v in anno.items():
                        origin,args = self._type2optional(k,v,optionals)
                        defaults.setdefault(k,self._type2default(v,origin,args))
                defaults.update(originDefaults)  ## ==== 原本的默认值也加入考虑
                for k,v in cls.__dict__.items():
                    if k.endswith("__") or callable(v) or isinstance(v,(classmethod,property)): # 不管双下划线、可调用对象、property
                        continue
                    defaults[k]=v
                    if v is None:
                        optionals.add(k)  # 默认值为 None 代表可选
                self._defaults=defaults
                if optionals:
                    self._optionals=optionals
            return defaults

        _defaults=_defaults.setter(clsDefaults.fset) # setter 不变

        newMembers["_defaults"]=_defaults

    # @classmethod
    # def setDictProperties(meta,cls:type,self:dict,anno=None): # 新类创建后再往里加
    #     if anno is None:
    #         try:
    #             anno:dict[str,type]=inspect.get_annotations(cls,eval_str=True) # 延迟求类型标注
    #         except (NameError,TypeError):
    #             logger.opt(exception=True).error("无法推断类型标注")
    #             return None
    #     logger.debug(f"{cls.__name__}  {anno}")
    #     try:
    #         meta._initings.add(cls) # 一定程度上防止递归，下面的 setattr(self...) 可能再次触发此方法
    #         for k,v in anno.items():
    #             if isinstance(v,type):
    #                 v=get_origin(v) or v
    #                 if issubclass(v,Mapping) and v is not dict: # v 是 Mapping 非 dict 的子类
    #                     pvalue=getattr(cls,k,None)
    #                     if not pvalue or (isinstance(pvalue,property) and not getattr(pvalue.fset,"_dictProp",None)): 
    #                         # 不反复设置类的属性                                 # 有这个字段就是设置过的
    #                         pvalue=meta.keyDictProperty(k,v)
    #                         setattr(cls,k,pvalue) # 设置属性
    #                         # logger.debug(f"设置 {k}  {v}")
    #                         if not isinstance(kval:=self.get(k,{}),v): # 默认值为 {}
    #                             setattr(self,k,kval) # 更新属性值
    #     finally:
    #         meta._initings.remove(cls)

    #     return anno

class UnitMeta(type):

    DictCls=UnitDict

    _classes:dict[str,type[DictCls]]={}
    
    def __new__(meta,name:str,bases:tuple,members:dict[str,Any],pattern:type=None,**kw):
        if newCls:=meta._classes.get(name):
            return newCls

        members.setdefault("__doc__",None)
        while origin:=get_origin(pattern):
            pattern, docs=deAnnotated(pattern, origin, args=None)
            if docs:  # 是 Annotated
                if originDoc:=members["__doc__"]:
                    members["__doc__"] = "\n".join(chain(docs, (originDoc,)))
                else:
                    members["__doc__"] = "\n".join(docs)
            elif origin is dict and len(args:=get_args(pattern))>1:  # dict[xxx,pattern]
                pattern=args[1]
            else:
                pattern=origin or pattern
        if not isinstance(pattern,type):
            raise ValueError(f"{pattern=} is not a type")
        if not isBuiltinType(pattern) and not issubclass(pattern,ConfigDict):
            pattern=ConfigMeta.mimic(pattern)
            frame:FrameType=members.pop("__last_frame__",None)
            if frame is not None:
                frame.f_locals[pattern.__name__] = pattern
        # if not issubclass(pattern,ConfigDict):  pattern 是 str 啥的可能会出问题
        #     pattern=ConfigMeta.mimic(pattern)
        
        defaultsDict:ClassDict=meta.setMembers(members,pattern)
        # meta._setInit(members,pattern)
        newCls=super().__new__(meta,name,(meta.DictCls,*meta.DictCls.__bases__,*bases),members)
        defaultsDict.setFunc=newCls
        meta._classes[name]=newCls
        return newCls

    @classmethod
    def setMembers(meta, members:dict[str,Any], pattern:type):
        members["__pattern__"]=pattern
        members["__pattern_default__"]=None
        defaultsDict=ClassDict(setFunc=UnitDict) # 占位
        members["__default_values__"]=defaultsDict
        members["__annotations_evaled__"]=ClassDict(setFunc=functools.partial(defaultdict,just(pattern)))
        # 类型标注默认返回 pattern
        return defaultsDict

    # @classmethod
    # def _setInit(meta, members:dict[str,Any], pattern:type):
    #     def __init__(self,map=None, / ,**ikw):
    #         ikw.pop("pattern",None)
    #         meta.DictCls.__init__(self, map, pattern=pattern, **ikw)
        
    #     members["__init__"]=functools.wraps(meta.DictCls.__init__)(__init__)
UnitDictSubType=NewType("UnitDictSubType",UnitDict)

class Unit:

    def __new__(cls,name:str,pattern:type,doc:str=None) -> type[UnitDictSubType]:
        frame=inspect.currentframe().f_back
        return UnitMeta(name,(),{ "__doc__":doc, "__last_frame__":frame },pattern=pattern)
    
    @classmethod
    def addDefault(cls,name:str,key:str,val=Undefined,anno=Undefined):
        if unitCls:=UnitMeta._classes.get(name):
            unitCls.addDefault(key,val,anno)
        else:
            raise KeyError(f"Unit {name=} not exists")

    