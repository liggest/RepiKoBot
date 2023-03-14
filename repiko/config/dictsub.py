from __future__ import annotations

from typing import is_typeddict, get_origin, get_args, Union, Literal, Mapping, Annotated, Iterable, Any
from typing_extensions import Required, NotRequired
from types import UnionType, NoneType

from itertools import chain

from repiko.config.util import get_annotations, Undefined, deAnnotated, indent, ClassDict, isBuiltinType
# import repiko.config.meta as meta

class ConfigDict(dict):

    # defaultedSet=set()

    def __init__(self,map=None, / ,pattern:type=None,patternLocal:dict=None, **kw):

        self.__pattern__=pattern
        self.__patternLocal__=patternLocal

        if map is None:
            super().__init__(**kw)
        else:
            super().__init__(map,**kw)

    def __repr__(self):
        if self.__pattern__:
            return f"{self.__pattern__.__name__}({super().__repr__()})"
        return super().__repr__()
        

    def __getitem__(self, key):
        if (optionals:=self._optionals) and key in optionals:
            if (item:=super().get(key)) is None:
                return item
        else:
            item=super().__getitem__(key)
        newItem=self._handleItem(key, item)
        if newItem is not item:
            super().__setitem__(key,newItem)
        return newItem

    # def __setitem__(self, key, value) -> None:
    #     return super().__setitem__(key, value)

    def _handleItem(self,key,item):
        itemCheck=item is None or isinstance(item,Mapping) # 为 None 或 Mapping 时，可能能替换为默认值
        if itemCheck:
            if isinstance(item,(ConfigDict,UnitDict)): # item 本体或默认值
                # return item if item else item._defaults
                return item
            clsCheck=(
                self.__pattern__ and 
                (defaults:=self._defaults) and 
                (defaultItem:=dict.get(defaults,key,Undefined)) is not Undefined) # key 有默认值
                # (defaultItem:=super(defaults.__class__,defaults).get(key,Undefined)) is not Undefined) # key 有默认值
            if clsCheck:
                anno=self._anno
                if anno and (itemCls:=anno.get(key)): # key 有注解
                    itemOrigin=get_origin(itemCls)
                    DictCls=ConfigDict
                    if itemOrigin in (Union, UnionType, Required, NotRequired, Annotated) and (itemArgs:=get_args(itemCls)):
                        any(DictCls:=c for c in itemArgs if isinstance(c,type) and issubclass(c,(ConfigDict,UnitDict)))
                        # args 中第一个 ConfigDict 子类
                    itemCls=itemOrigin or itemCls
                    if isinstance(itemCls,type) and issubclass(itemCls,(ConfigDict,UnitDict)): # 注解本身是 ConfigDict 子类
                        DictCls=itemCls
                    # items={**defaultItem,**item} if item else defaultItem # item 有内容时覆盖上去
                    # return DictCls(items,pattern=itemCls)
                    item = defaultItem if item is None else item
                    return DictCls(item, pattern=itemCls)
                # return defaultItem
        return item

    def get(self,key,default=None):
        if (item:=super().get(key,Undefined)) is Undefined:
            return default
        newItem=self._handleItem(key, item)
        if newItem is not item:
            super().__setitem__(key,newItem)
        return newItem
        
    # def _getDefaults(self) -> ConfigDict:
    #     cls=self.__pattern__
    #     anno=self._anno
    #     defaults=getattr(cls,"__default_values__",None) or self._emptyCopy
    #     if anno:
    #         for k,v in anno.items():
    #             defaults.setdefault(k,self._type2default(v))
    #     for k,v in cls.__dict__:
    #         if k.endswith("__") or callable(v) or isinstance(v,(classmethod,property)): # 不管双下划线、可调用对象、property
    #             continue
    #         defaults[k]=v
    #     return defaults

    def _type2optional(self,k,v,optionals:set):
        origin = get_origin(v)
        args = None
        
        if v is NoneType:
            optionals.add(k)
        elif origin is NotRequired:
            optionals.add(k)
        elif origin in (Union, UnionType):
            args = get_args(v)
            for a in args:
                self._type2optional(k,a,optionals)
        elif origin is Annotated:
            args = get_args(v)
            v,*_ = args
            self._type2optional(k,v,optionals)
        return origin, args

    def _type2default(self,v,origin=Undefined,args=None):
        if is_typeddict(v):
            return ConfigDict(pattern=v)._defaults
        # if v in meta.ConfigMeta._classes:
        #     return v()
        if origin is Undefined:
            origin = get_origin(v)  # Literal[3] => Literal
        if args is None:
            args = get_args(v)      # Literal[3] => (3,)
        vO=origin or v
        if origin is Literal and args:
            if len(args)==1:
                return args[0]
            else: 
                return args   # 如果长度不为 1，以元组形式返回
        elif origin in (Union, UnionType, Required, NotRequired, Annotated) and args:
            return self._type2default(args[0]) # Union 中的第一项
        elif isinstance(vO,type) and issubclass(vO, (ConfigDict,UnitDict)):
            return vO()._defaults
        elif isinstance(vO,type) or callable(vO): # callable 范围太广了...
            return vO()
        return v

    @property
    def _emptyCopy(self):
        # if not self:
        #     return self
        return self.__class__(pattern=self.__pattern__, patternLocal=self.__patternLocal__)

    # def copy(self):
    #     new=self._emptyCopy
    #     super(new.__class__,new).__init__(self)
    #     return new

    @property
    def _defaults(self):
        cls=self.__pattern__
        if not cls:
            return self._emptyCopy

        # if self.defaultedSet and cls in self.defaultedSet:
        #     return self._emptyCopy

        defaults:ConfigDict=getattr(cls,"__default_values__",None)
        if defaults is None:
            defaults=self._emptyCopy
            self._defaults=defaults # 防止递归
            # defaults=self._getDefaults()
            anno=self._anno
            optionals=None
            if anno:
                optionals=set()  # 当做没有初始化 _optionals
                for k,v in anno.items():
                    origin,args = self._type2optional(k,v,optionals)
                    defaults.setdefault(k,self._type2default(v,origin,args))
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

    @_defaults.setter
    def _defaults(self,val):
        cls=self.__pattern__
        if not cls:
            raise AttributeError("No pattern in ConfigDict")
        setattr(cls,"__default_values__", val if val is not None else self._emptyCopy )

    @property
    def _anno(self) -> dict[str,type]:
        cls=self.__pattern__
        if not cls:
            return {}
        
        if getattr(cls,"__annotations_evaled__",False):
            return cls.__annotations__
        anno=get_annotations(cls,locals=self.__patternLocal__,eval_str=True)
        self._anno=anno
        return anno

    @_anno.setter
    def _anno(self,val):
        cls=self.__pattern__
        if not cls:
            raise AttributeError("No pattern in ConfigDict")
        
        if val:
            cls.__annotations__= val
            setattr(cls,"__annotations_evaled__",True)
    
    @property
    def _optionals(self) -> set:
        """  值可选的键的集合  """
        cls=self.__pattern__
        if not cls:
            return None
        
        return getattr(cls,"__optional_keys__",None)

    @_optionals.setter
    def _optionals(self,val):
        cls=self.__pattern__
        if not cls:
            raise AttributeError("No pattern in ConfigDict")
        
        print("======",self.__class__,val)
        setattr(cls,"__optional_keys__",val)

    def _docsGen(self,haddoc=None,level=0):
        cls=self.__pattern__
        if not cls:
            return
        
        if haddoc is None:
            haddoc=set()
        if cls in haddoc:
            return
        else:
            haddoc.add(cls)

        if cls.__doc__:
            yield from indent(cls.__doc__.splitlines(),level=level)

        anno=self._anno
        if not anno:
            return
        
        for k,v in anno.items():
            yield from self._type2doc(k,v,haddoc,level)
    
    def _type2doc(self,k,v,haddoc,level=0) -> Iterable[str]:
        if isinstance(v,type):
            if is_typeddict(v) or (issubclass(v,ConfigDict)):
                return chain(indent((k,),level=level), ConfigDict(pattern=v)._docsGen(haddoc=haddoc, level=level+1))
            if issubclass(v,UnitDict):
                return chain(indent((k,),level=level), v()._docsGen(haddoc=haddoc, level=level+1))
        
        origin, args=get_origin(v), get_args(v)  # Literal[3] => Literal  (3,)
        if origin in (Union, UnionType, Required, NotRequired) and args:
            return self._type2doc(k,args[0],haddoc,level)  # Union 中的第一项
        vAnno, annoDocs=deAnnotated(v,origin,args)
        if annoDocs:  # 是 Annotated 才有，否则为 None
            vAnnoDocs=self._type2doc(k,vAnno,haddoc,level)
            try:
                firstLine=next(vAnnoDocs)
                return chain((firstLine,), indent(annoDocs,level=level+1),vAnnoDocs)
            except StopIteration:
                return chain(indent((k,),level=level), indent(annoDocs,level=level+1)) # vAnnoDocs 一行也没有
        if origin is Literal and args:
            return indent((f"{k}  {','.join(repr(a) for a in args)  }",),level=level)
        v=origin or v
        return indent((f"{k}  {v.__name__}",),level=level)

    # def __enter__(self):
    #     self.defaultedSet.clear()
    #     self.defaultedSet.add(None) # 保证有值
    #     return self

class UnitDict(dict):

    __pattern__:type=None
    __pattern_default__=None
    __default_values__=ClassDict()
    __annotations_evaled__=ClassDict()

    def __init__(self,map=None, / , **kw):

        kw.pop("pattern",None)
        kw.pop("patternLocal",None)

        if map is None:
            super().__init__(**kw)
        else:
            super().__init__(map,**kw)

    def __repr__(self):
        if self.__pattern__:
            return f"{self.__class__.__name__}({super().__repr__()})"
        return super().__repr__()

    _handleItem=ConfigDict._handleItem

    def __getitem__(self, key):
        item=super().__getitem__(key)
        newItem=self._handleItem(key, item)
        if newItem is not item:
            super().__setitem__(key,newItem)
        return newItem

    def get(self,key,default=None):
        if (item:=super().get(key,Undefined)) is Undefined:
            return default
        newItem=self._handleItem(key, item)
        if newItem is not item:
            super().__setitem__(key,newItem)
        return newItem

    @property
    def _defaults(self) -> Mapping:
        return self.__default_values__
    
    @_defaults.setter
    def _defaults(self,val):
        self.__default_values__=val

    @property
    def _anno(self) -> dict[str,type]:
        return self.__annotations_evaled__

    @_anno.setter
    def _anno(self,val):
        self.__annotations_evaled__=val

    @classmethod
    def addDefault(cls,key,val=Undefined,anno=Undefined):
        if anno is Undefined:  # 无 anno
            if val is Undefined:
                raise ValueError(f"Can't add default {key=}. No val & no anno")
            
            cls.__default_values__[key]=cls._defaultWithPattern(val)
            if not cls.__pattern__ or isinstance(val,cls.__pattern__):
                cls.__annotations_evaled__[key]=type(val)
            else:
                cls.__annotations_evaled__[key]=cls.__pattern__
        elif get_origin(anno) or isinstance(anno,type):   # 合法的 anno
            cls.__annotations_evaled__[key]=anno
            cls.__default_values__[key]=cls._defaultWithPattern(val) if val is not Undefined else cls._type2default(anno)
        else:
            ValueError(f"{anno=} is not an annotation")

    _type2default=classmethod(ConfigDict._type2default)

    @classmethod
    def _defaultWithPattern(cls,val):
        if isinstance(val,Mapping) and issubclass(cls.__pattern__,(ConfigDict,UnitDict)):
            if cls.__pattern_default__ is None:
                cls.__pattern_default__=cls.__pattern__()._defaults
            return { **cls.__pattern_default__, **val }
        return val

    def _docsGen(self,haddoc=None,level=0):
        cls=self.__pattern__
        if not cls:
            return

        if haddoc is None:
            haddoc=set()
        if cls in haddoc:
            return
        else:
            haddoc.add(cls)

        defaults=self._defaults
        if not defaults:
            return

        if self.__doc__:
            yield from indent(self.__doc__.splitlines(),level=level)
            yield ""  # 空行

        name=cls.__name__
        if not isBuiltinType(cls) and cls.__doc__:  # 不输出内建类型的文档
            yield from indent((name,),level=level)
            yield from indent(cls.__doc__.splitlines(),level=level+1)
            yield ""  # 空行

        anno=self._anno
        for k in defaults:
            if (v:=anno.get(k)) and v is not cls:
                yield from self._type2doc(k,v,haddoc,level)
            else:
                yield from indent((f"{k}  {name}",),level=level)
        # yield from indent( (f"{k}  { anno[k].__name__ if k in anno else name }" for k in defaults) ,level=level)

    _type2doc=ConfigDict._type2doc
