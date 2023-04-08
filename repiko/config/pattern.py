from __future__ import annotations

import types
import inspect
from dataclasses import dataclass, field
from itertools import chain

from typing import Literal, Union, Mapping, MutableMapping, Callable, Generator, Annotated, Any
from typing import TYPE_CHECKING, ForwardRef, TypeVar
from typing import get_origin, get_args, is_typeddict
from typing_extensions import Required, NotRequired, Self
from types import UnionType, NoneType, FrameType

from repiko.config.util import Undefined, get_annotations, indent, RecursionGuard
from repiko.core.log import logger

# class PatternDictMeta(type):
#     pass

@dataclass
class Field:
    """  Pattern 子类中的字段  """
    
    name:str = ""
    _annotation:type = Undefined
    _default:Any = Undefined
    _optional:bool = field(default=None, init=False, compare=False)
    _container:FieldContainer = field(default=None, init=False, repr=False, compare=False)
    
    _containerGetter:Callable[[],FieldContainer] = field(default=None, init=False, repr=False, compare=False)

    _doc:list[str] = field(default=None, init=False, compare=False)

    @property
    def container(self):
        if not self._container:
            if not self._containerGetter:
                raise ValueError("FieldContainer 不存在")
            self._container = self._containerGetter()
            del self._containerGetter
        return self._container

    def withContainer(self, objOrGetter: FieldContainer | Callable[[],FieldContainer]):
        if isinstance(objOrGetter, FieldContainer):
            self._container = objOrGetter
        elif callable(objOrGetter):
            self._containerGetter = objOrGetter
        return self

    @property
    def annotation(self):
        if self._annotation is Undefined and (container := self.container):
            self._annotation = container.annotations.get(self.name,container.__defaultAnnotation__)
            self.annotation = TypeHelper.filterClass(self._annotation)  # 这里也会修改 container 的 __annotations__
        return self._annotation
    
    @annotation.setter
    def annotation(self, val:type):
        self._annotation = val
        if val is not Undefined and (container := self.container):
            container.annotations[self.name] = val
    
    @annotation.deleter
    def annotation(self):
        self._annotation = Undefined

    @property
    def default(self):
        if self._default is Undefined:
            self._default = TypeHelper.toDefault(self.annotation)
        return self._default

    @property
    def optional(self):
        if self._optional is None:
            self._optional = TypeHelper.isOptional(self.annotation) or self.default is None
        return self._optional
    
    @optional.setter
    def optional(self,val):
        self._optional = bool(val)

    def doc(self, level=0, haddoc:set=None):
        self._doc = []
        key = self.name
        if self.optional:
            key = f"{key}  [可选]"
        self._doc.extend( TypeHelper.toDoc(key, self.annotation, level, haddoc) )
        return self._doc

    # def ensure(self):
    #     if self.default is Undefined:
    #         self.default = TypeHelper.toDefault(self.annotation)
    #         # self.optional = TypeHelper.isOptional(t)
    #     # self.optional = self.optional or self.default is None
    #     return self


# class PatternContainer:
#     pass

class FieldContainer:
    """  
        容纳提供类型标注（__annotation__）的类和字段（fields）\n
    """

    def __init__(self, cls:type[MutableMapping] | PatternMeta):
        if not hasattr(cls, "__annotations__"):
            raise ValueError(f"{cls!r} 没有 __annotations__")
        self.__pattern__ = cls
        if isinstance(cls, PatternMeta):
            if cls.__fields__:
                self.__fields__ = cls.__fields__
                del cls.__fields__  # 移动暂存的 fields

    # __dictClass__ = dict
    __fields__:dict[str,Field] = None
    __defaultAnnotation__:type = Undefined

    @property
    def fields(self):
        if self.__fields__ is None:
            self.__fields__ = {}
        return self.__fields__
    
    @fields.deleter
    def fields(self):
        del self.__fields__

    @property
    def _defaults(self):
        return self.__pattern__( ( (k,v.default) for k,v in self.fields.items() ) )

    # @property
    # def _defaultsNoOptionals(self):
    #     return self.__pattern__( ( (k,v.default) for k,v in self.fields.items() if not v.optional) )

    __creatingFrame__:FrameType = None
    
    @property
    def annotations(self)  -> dict[str,type]:
        cls = self.__pattern__
        untyped = any(isinstance(v,(str, ForwardRef)) for v in cls.__annotations__.values())
        if untyped:
            local = self.__creatingFrame__.f_locals if self.__creatingFrame__ else None
            cls.__annotations__ = get_annotations(cls,locals=local,eval_str=True)
        return cls.__annotations__

T = TypeVar("T")

class PatternMeta(type):
    
    _mimiced:dict[type, PatternMeta] = {}

    @classmethod
    def mimic(meta, cls:T, frame:FrameType=None) -> Self | T:
        """  得到 cls 和 Pattern 的子类  """
        if issubclass(cls,Pattern):
            return cls
        if mimiced := meta._mimiced.get(cls):
            return mimiced
        mimiced:PatternMeta = types.new_class(cls.__name__, 
                               TypeHelper.filterBases((Pattern, cls)), 
                               { "metaclass":meta }, 
                               lambda ns : ns.update(cls.__dict__))
        mimiced._container.__creatingFrame__ = frame or inspect.currentframe().f_back
        meta._mimiced[cls] = mimiced
        return mimiced

    # @classmethod
    # def __prepare__(meta, name:str, bases:tuple[type, ...], **kw) -> Mapping[str, object]:
    #     members=super().__prepare__(name, bases, **kw)
    #     print(name,bases,members)
    #     return members

    def __new__(meta, name: str, bases: tuple, members: dict[str,Any], **kw):
        if bases and bases[0] is dict: # dict 的直接子类，即 Pattern
            return super().__new__(meta, name, bases, members, **kw)
        members.pop("__dict__",None)
        members.pop("__weakref__",None)
        
        annos:dict = members.get("__annotations__",{})
        cls = None

        def containerGetter():
            return cls and cls._container

        newMembers = meta.setProperties(name,members,annos,containerGetter)
        cls = super().__new__(meta,name,bases,newMembers,**kw)
        # logger.debug((name,bases,members))
        logger.debug(f"Pattern {name}")
        return cls

    def __init__(cls, name: str, bases: tuple, members: dict[str,Any], **kw):
        if bases and bases[0] is not dict: # 非 dict 直接子类，即 Pattern 子类
            cls._container = FieldContainer(cls)  # 让类型提示不是 Self
            # cls._container.__dictClass__ = cls
            cls._container.__creatingFrame__ = inspect.currentframe().f_back
            # if cls.__fields__:
            #     for field in cls.__fields__.values():
            #         field.container = cls
        super().__init__(name,bases,members,**kw)

    @staticmethod
    def keyProperty(key:str, anno:str|type):
            
        def kget(self) -> anno:
            try:
                return self[key]
            except KeyError as e:
                raise AttributeError(f"{self!r} 中不存在 {key!r}") from e # 当作发出 AttributeError

        def kset(self,val:anno):
            self[key] = val
        def kdel(self):
            del self[key]
        if key == "bot":
            pass
        return property(kget,kset,kdel,f"self[{key!r}]")

    @classmethod
    def setProperties(meta, name:str, members:dict[str,Any], annos:dict[str,str|type], 
                      getter:Callable[[],FieldContainer]) -> tuple[dict[str,Any], dict[str,Any]]:
        # defaults = {}
        fields:dict[str,Field] = {}
        # optionals = set()

        def membersGen(): # 过滤 members 中的项
            for k,v in annos.items():
                if k.endswith("__"): # 不管双下划线
                    continue
                if isinstance(v,(str, ForwardRef)):
                    fields[k] = Field(k).withContainer(getter)
                else:
                    fields[k] = Field(k,v).withContainer(getter)
                if k not in members: # 只有注解的
                    yield k, meta.keyProperty(k,v) # 变成属性

            for k,v in members.items():
                # if v is None:
                #     optionals.add(k)
                if isinstance(v,type) and not TypeHelper.isBuiltin(v) and not issubclass(v,Pattern): # 非内建类、非已装饰过的
                    if name:
                        parentName = v.__qualname__.removesuffix(v.__name__)
                        if parentName.endswith(f"{name}."): # parent 的内部类
                            yield k, meta.mimic(v)  # 内部类都装饰一下
                elif callable(v) or isinstance(v,(classmethod,property)): # 不管可调用对象、property
                    yield k,v
                elif k.endswith("__"): # 双下划线字段原封不动
                    yield k,v
                else:  # 待收集字段
                    if field := fields.get(k):
                        field._default = v
                    else:
                        field = Field(k,_default=v).withContainer(getter)
                    if v is None:
                        field._optional = True
                    fields[k] = field
                    anno = annos.get(k,Any) # 默认注解 Any
                    # defaults[k]=v
                    yield k, meta.keyProperty(k,anno) # 变成属性

            # yield "__default_values__", defaults
            # yield "__optional_keys__", optionals
            if fields:
                yield "__fields__", fields
        
        newMembers = dict(membersGen())
        return newMembers # 返回 newMembers

    __fieldContainer__:FieldContainer = None
    __fields__:dict[str,Field] = None

    @property
    def _container(cls) -> FieldContainer:
        if cls.__fieldContainer__ is None:
            cls.__fieldContainer__ = FieldContainer(cls)
        return cls.__fieldContainer__
    
    @_container.setter
    def _container(cls,val):
        if not isinstance(val, FieldContainer):
            val = FieldContainer(val)
        cls.__fieldContainer__ = val
        
    @property
    def _fields(cls):
        """  所有字段，方便用类查看  """
        return cls._container.fields
    
    # @property
    # def _emptyCopy(cls) -> Self:
    #     return cls()
    
    @property
    def _defaults(cls):
        """  默认值，方便用类查看  """
        container = cls._container
        if not container or RecursionGuard.has(cls):
            # return cls._emptyCopy
            return cls()
        with RecursionGuard(cls):
            return container._defaults
    
    @property
    def _defaultsNoOptionals(cls):
        """  不含可选字段的默认值  """
        container = cls._container
        if not container or RecursionGuard.has(cls):
            return cls()
        with RecursionGuard(cls):
            return cls(TypeHelper.defaultsNoOptionalsGen(container.fields))
    
    @property
    def defaultAnnotation(self):
        """  所有字段的默认类型，初始时未定义  """
        return self._container.__defaultAnnotation__
    
    @defaultAnnotation.setter
    def defaultAnnotation(self, val:type):
        self._container.__defaultAnnotation__ = val

class Pattern(dict, metaclass=PatternMeta):
    """  用来定义配置各字段的类型、默认值等  """
    
    if TYPE_CHECKING:
        _defaults:Self
        _defaultsNoOptionals:Self

    def __init__(self, data=None, /, **kw):
        if data is None:
            super().__init__(**kw)
        else:
            super().__init__(data,**kw)

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __setattr__(self, name:str, value):
        if not (name.endswith("__") or hasattr(self.__class__, name)): # 不管双下划线、不反复设置类的字段
            prop = PatternMeta.keyProperty(name,Any)
            setattr(self.__class__,name,prop) # 给类设置属性
        super().__setattr__(name,value)

    @classmethod
    def addDefault(cls, key:str, default=Undefined, annotation:type=Undefined):
        container = cls._container
        if annotation is not Undefined:
            container.annotations[key] = annotation  # 类型标注设给 __annotations__，如果 field 需要用再从那里拿
        if field := container.fields.get(key):
            field._default = default
            del field.annotation
            # field._annotation = annotation
        else:
            container.fields[key] = Field(key,_default=default).withContainer(container)

    @classmethod
    def _docsGen(cls, level=0, haddoc:set=None):
        container = cls._container
        pattern = container.__pattern__
        if haddoc is None:
            haddoc = set()
        if pattern in haddoc:
            return
        else:
            haddoc.add(pattern)
        
        if pattern.__doc__:
            yield from indent(pattern.__doc__.splitlines(),level=level)
        
        if container.__fields__:
            for v in container.__fields__.values():
                yield from v.doc(level, haddoc)

    @property
    def __fieldContainer__(self):
        return self.__class__._container

    # @classmethod
    # def _emptyCopy(cls):
    #     # return self.__class__(pattern=self.__class__.__pattern__, patternLocal=self.__patternLocal__)
    #     return cls()

    # @property
    # def _defaults(self) -> Self:
    #     cls = self.__fieldContainer__
    #     if not cls:
    #         return self._emptyCopy
        
    #     return cls._defaults

    def __getitem__(self, key):
        field = self.__fieldContainer__.fields.get(key)
        if field and field.optional:
            if (item := super().get(key)) is None: # 可选的项在不存在时可以返回 None
                return item
        else:
            item = super().__getitem__(key)
        newItem = self._handleItem(key,item)
        if newItem is not item:
            super().__setitem__(key,newItem)
        return newItem

    def _handleItem(self, key, item):
        itemCheck = item is None or isinstance(item,Mapping) # 为 None 或 Mapping 时，可能能替换为默认值
        if not itemCheck:
            return item
        if isinstance(item, Pattern): # item 本体
            # return item if item else item._defaults
            return item
        fieldCheck=(
            (cls := self.__fieldContainer__) and
            (field := cls.fields.get(key)) and
            # (defaults:=self._defaults) and 
            ((defaultItem := field.default) is not Undefined) # key 有默认值
            # (defaultItem:=super(defaults.__class__,defaults).get(key,Undefined)) is not Undefined) # key 有默认值
        )
        if not fieldCheck:
            return item
        itemCls = field.annotation
        if itemCls is Undefined:
            return item
        itemOrigin = get_origin(itemCls)
        item = defaultItem if item is None else item
        dictCls = None
        candidates = []
        if itemOrigin in (Union, UnionType, Required, NotRequired, Annotated) and (itemArgs := get_args(itemCls)):
            candidates.extend(itemArgs)
        candidates.append(itemCls)
        if any(dictCls := c for c in candidates if isinstance(c,type) and issubclass(c,Mapping)):
            return dictCls(item)
        return item
        # anno=cls.annos
        # if anno and (itemCls := anno.get(key)): # key 有注解
        #     itemOrigin=get_origin(itemCls)
        #     DictCls=ConfigDict
        #     if itemOrigin in (Union, UnionType, Required, NotRequired, Annotated) and (itemArgs:=get_args(itemCls)):
        #         any(DictCls:=c for c in itemArgs if isinstance(c,type) and issubclass(c,(ConfigDict,UnitDict)))
        #         # args 中第一个 ConfigDict 子类
        #     itemCls=itemOrigin or itemCls
        #     if isinstance(itemCls,type) and issubclass(itemCls,(ConfigDict,UnitDict)): # 注解本身是 ConfigDict 子类
        #         DictCls=itemCls
        #     # items={**defaultItem,**item} if item else defaultItem # item 有内容时覆盖上去
        #     # return DictCls(items,pattern=itemCls)
        #     item = defaultItem if item is None else item
        #     return DictCls(item, pattern=itemCls)
        # # return defaultItem
        # return item

    def get(self, key, default=None):
        if (item := super().get(key,Undefined)) is Undefined:
            return default
        newItem = self._handleItem(key,item)
        if newItem is not item:
            super().__setitem__(key,newItem)
        return newItem

    # def _updateWith(self, data:Mapping):
    #     self.update(data)
    #     return self

class TypeHelper:

    @staticmethod
    def replaceClass(oriT:type, newT:PatternMeta):
        import sys
        mGlobals = sys.modules[oriT.__module__].__dict__
        if oriT.__name__ in mGlobals:
            mGlobals[oriT.__name__] = newT

    @classmethod
    def filterClass(cls, t:type):
        newT = t
        if is_typeddict(t):
            newT = Pattern.mimic(t)  # 用 PatternMeta 的话编辑器类型识别不出来
            cls.replaceClass(t,newT)
        elif mimiced := PatternMeta._mimiced.get(t):  # 变成装饰后的类
            newT = mimiced
        return newT

    @classmethod
    def toDefault(cls, t:type):
        # t = cls.filterClass(t)  # 暂时没必要
        origin, args = get_origin(t), get_args(t)  # Literal[3] => Literal  (3,)
        tOri = origin or t
        if origin is Literal and args:
            return args[0] if len(args) == 1 else args   # 如果字面量长度不为 1，如 Literal[1,2,3]，则以元组形式返回
        elif origin in (Union, UnionType, Required, NotRequired, Annotated) and args:
            return cls.toDefault(args[0])  # Union 中的第一项的默认值
        elif isinstance(tOri,type):
            if issubclass(tOri, Pattern):
                return tOri._defaults
            return tOri()  # 假设无参数能得到类的默认值
        elif callable(tOri):  # callable 范围太广了...
            return tOri()
        return t

    @classmethod
    def isOptional(cls, t:type) -> bool:
        origin, args = get_origin(t), get_args(t)
        if t is NoneType or origin is NotRequired:
            return True
        elif origin in (Union, UnionType):
            return any(cls.isOptional(a) for a in args)
        elif origin is Annotated:
            a,*_ = args
            return cls.isOptional(a)
        return False

    @classmethod
    def defaultsNoOptionalsGen(cls, fields:dict[str,Field]):
        for k,v in fields.items():
            if v.optional:
                continue
            if v._default is not Undefined and isinstance(v._default,Pattern):
                yield k, v._default.__class__._defaultsNoOptionals
            elif t := v.annotation:
                origin, args = get_origin(t), get_args(t)
                tOri = origin or t
                if origin in (Union, UnionType, Required, NotRequired, Annotated) and args:
                    tOri = args[0]
                if isinstance(tOri,type) and issubclass(tOri,Pattern):
                    yield k, tOri._defaultsNoOptionals
                    continue
            yield k, v.default

    @classmethod
    def toDoc(cls, key:str, t:type, level=0, haddoc:set=None):
        if t is Undefined:
            return indent((key,),level=level)
        if isinstance(t,type) and issubclass(t,Pattern):
            return chain(indent((key,),level=level), t._docsGen(level=level+1, haddoc=haddoc))
        
        origin, args = get_origin(t), get_args(t)  # Literal[3] => Literal  (3,)
        if origin in (Union, UnionType, Required, NotRequired) and args:
            return cls.toDoc(key,args[0],level,haddoc)  # Union 中的第一项
        tInner, annoDocs = cls.deAnnotated(t,origin,args) # Annotated[tInner,...]
        if annoDocs:  # Annotated 才有，否则为 None
            tInnerDocs = cls.toDoc(key,tInner,level,haddoc) # tInner 的文档
            try:
                firstLine = next(tInnerDocs)
                return chain((firstLine,), indent(annoDocs,level=level+1), tInnerDocs)
            except StopIteration:
                return chain(indent((key,),level=level), indent(annoDocs,level=level+1)) # tInnerDocs 一行也没有
        if origin is Literal and args:
            return indent((f"{key}  {','.join(repr(a) for a in args)  }",),level=level)
        t = origin or t
        return indent((f"{key}  {t.__name__}",),level=level)

    @staticmethod
    def isBuiltin(t:type):
        """  对内建类型的不完全收集  """
        return t in { object, int, float, complex, str, bytes, bool, slice, tuple, list, dict, set, range }
    
    @staticmethod
    def filterBases(bases:tuple):
        return tuple(base for base in bases if not is_typeddict(base))

    @classmethod
    def deAnnotated(cls, t:type, origin=Undefined, args=Undefined):
        """
            为 cls 去除 Annotated 包装\n
            cls 是 Annotated 则返回 被包装的类, docs（生成器）\n
            否则返回 cls, None
        """
        if origin is Undefined:
            origin = get_origin(t)
        if args is Undefined:
            args = get_args(t)
        if origin is not Annotated:
            return t, None
        t, *items = args
        return t, cls.annotatedDocsGen(items)

    @classmethod
    def annotatedDocsGen(cls, docItems:tuple) -> Generator[str,None,None]:
        """  生成器，逐一输出 Annotated[..., docItems] 中的文档  """
        for i in docItems:
            if isinstance(i,str):
                yield from i.splitlines()
            elif args := get_args(i): # Literal["xxx"]
                yield from cls.annotatedDocsGen(args)


# class PatternDict(metaclass=PatternDictMeta):
#     pass

if __name__ == "__main__":

    from typing import TypedDict

    class CFG(Pattern):

        a:int = 3
        b:str
        c:list = None

        class ABS(Pattern):
            x:Literal[3]
            y:Annotated[Literal[5], "有注释看着就更长（"]

        abs:ABS | None

        class ADS:
            z:str = "6"
            w = "10"

        ads:ADS

    from pprint import pprint as print

    print(CFG._fields)
    assert CFG({ "a":10 }).a == 10
    defaults = CFG._defaults
    print(defaults)
    assert defaults.abs == CFG.ABS({ "x":3, "y":5 })
    assert CFG().abs is None
    print(CFG._fields)

    # print(Pattern.mro())
    # print(PatternMeta.mro(PatternMeta))
    # print(CFG.mro())
    # print(type.mro(type))

    @Pattern.mimic
    class CFG2(TypedDict):
        a:int
        b:CFG
        c:CFG3

    class CFG3(TypedDict):
        w:set
        h:tuple

    assert is_typeddict(CFG3)
    defaults2:CFG2 = CFG2._defaults
    assert issubclass(CFG3, Pattern)
    assert defaults2.c == { "w":set(), "h":() } == CFG3._defaults

    class CFG4(Pattern):
        pass

    CFG4.defaultAnnotation = CFG3
    CFG4.addDefault("a",default=1)
    CFG4.addDefault("b",default=2,annotation=int|None)
    CFG4.addDefault("c",default=3,annotation=Annotated[int|None,"这是 'c'"])
    CFG4.addDefault("d")
    CFG4.addDefault("e")
    CFG4.addDefault("f",default=None)

    cfg4 = CFG4()
    assert cfg4["b"] is None
    assert cfg4["c"] is None
    assert cfg4["f"] is None
    defaults4 = CFG4._defaults
    assert defaults4["a"] == 1
    assert defaults4["b"] == 2
    assert defaults4["c"] == 3
    assert defaults4["d"] == defaults4["e"] == CFG3._defaults
    assert defaults4["f"] is None
    cfg4 = CFG4({ "f":{} })
    assert isinstance(cfg4["f"],CFG3)
    assert cfg4["f"] == CFG3({})




    """

    PatternContainer

    defaults  : ?

    annos     : dict
    (frameLocal)

    optionals : set

    add(name,default,anno)

    ContainerMeta(type,PatternContainer)
    PatternMeta(type)

    Pattern(dict, metaclass=PatternMeta)

    __pattern__ : PatternContainer
    __getitem__
    get


    class Sub(Pattern):
    x:int
    y:int
    z:int

    Sub({})
    Sub["x"]
    Sub.x


    """

