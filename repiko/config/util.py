from __future__ import annotations

import inspect
import copy

from typing import TYPE_CHECKING, Callable, Mapping, MutableMapping #, get_origin, get_args, Generator
if TYPE_CHECKING:
    from repiko.core.bot import Bot

class _Undefined:
    """  None 有含义，不能作默认值时，用它作为未定义值的类型  """

    def __new__(cls):
        try:
            return Undefined
        except NameError:
            return super().__new__(cls)
        
    def __repr__(self) -> str:
        return "Undefined"

Undefined = _Undefined()

def looseGetattr(obj,name:str,default=None):
    """  在 obj 中寻找 `name`, `name.lower()` 和 `name.lower().strip("_")`  """
    n1=name.lower()
    n2=n1.strip("_")
    for n in (name,n1,n2):
        if (attr:=getattr(obj,n,Undefined)) is not Undefined:
            return attr
    return default

# def getClsDefaults(cls, extraLocals:dict=None):
#     defaults=getattr(cls,"__default_values__",None)
#     if defaults is None:
#         setattr(cls,"__default_values__",{})
#         defaults=_getClsDefaults(cls,extraLocals)
#         setattr(cls,"__default_values__",defaults)
#     return defaults

# def _getClsDefaults(cls, extraLocals:dict=None):
#     if not isinstance(cls,type):
#         cls=cls.__class__
#     anno=getClsAnnotations(cls,extraLocals)
#     defaults=getattr(cls,"__default_values__",{})
#     if anno:
#         for k,v in anno.items():
#             defaults.setdefault(k,_handleType(v))
#     for k,v in cls.__dict__:
#         if k.endswith("__") or callable(v) or isinstance(v,(classmethod,property)): # 不管双下划线、可调用对象、property
#             continue
#         defaults[k]=v
#     return defaults

# def getClsAnnotations(cls:type, extraLocals:dict=None):
#     if getattr(cls,"__annotations_evaled__",False):
#         return cls.__annotations__
#     anno=get_annotations(cls, locals=extraLocals, eval_str=True)
#     cls.__annotations__=anno
#     setattr(cls,"__annotations_evaled__",True)
#     return anno

# def _handleType(v):
#     if is_typeddict(v):
#         return getClsDefaults(v)
#     origin, args=get_origin(v), get_args(v) # Literal[3] => Literal  (3,)
#     if origin is Literal and args:
#         if len(args)==1:
#             return args[0]
#         else: 
#             return args   # 如果长度不为 1，以元组形式返回
#     elif origin in (Union, UnionType, Required, NotRequired) and args:
#         return _handleType(args[0]) # Union 中的第一项
#     elif isinstance(v,type) or callable(v): # callable 范围太广了...
#         return v()
#     return v

def eventDocsGen(eventName,bot:Bot,title:str=None):
    """  逐行生成 eventName 事件所有回调函数的文档字符串  """
    if not bot:
        return
    if (funcs:=bot.EM.get(eventName)) is None:
        return

    started=False
    for func in funcs:
        func:Callable
        if func and hasattr(func,"__doc__") and func.__doc__:
            if not started:
                if title:
                    yield from indent((title,),level=0)
                started=True
            yield from indent(func.__doc__.splitlines(),level=1)

# from typing import Annotated # , _AnnotatedAlias, TypeGuard

# def isAnnotated(cls) -> TypeGuard[_AnnotatedAlias]:
#     return isinstance(cls, _AnnotatedAlias)

# def deAnnotated(cls, origin=Undefined, args=None):
#     """
#         判断 cls 是否为 Annotated\n
#         是则返回 被包装的类, docs（生成器）\n
#         否则返回 cls, None
#     """
#     if origin is Undefined:
#         origin=get_origin(cls)
#     if args is None:
#         args=get_args(cls)
#     if origin is not Annotated:
#         return cls, None
#     cls,*items=args
#     return cls, annotatedDocsGen(items)


# def annotatedDocsGen(items:tuple) -> Generator[str,None,None]:
#     for i in items:
#         if isinstance(i,str):
#             yield from i.splitlines()
#         elif args:=get_args(i): # Literal["xxx"]
#             yield from annotatedDocsGen(args)

def indent(lines:list[str],level=0,length=4):
    # if isinstance(lines,str):
    #     lines=(lines,)
    if level==0:
        return (line.lstrip() for line in lines)      # 先把多余的缩进去除
    pad=" " * length * level
    return (f"{pad}{line.lstrip()}" for line in lines)

def just(val):
    return lambda: val

# def isBuiltinType(v:type):
#     """  对内建类型的不完全收集  """
#     return v in { object, int, float, complex, str, bytes, bool, slice, tuple, list, dict, set, range }

# class ClassDict:
#     """  作为类变量的延迟初始化字典（描述符）  """

#     def __init__(self,setFunc:Callable[[Mapping],Mapping]=None):
#         self.val:Mapping=None
#         self.setFunc=setFunc

#     def __get__(self, obj, cls=None):
#         if self.val is None:
#             self.__set__(obj,{})
#         return self.val
    
#     def __set__(self, obj, val):
#         if isinstance(val,Mapping):
#             if self.setFunc:
#                 self.val=self.setFunc(val)
#             else:
#                 self.val=val
#         else:
#             raise ValueError(f"{val=} is not Mapping")
        
#     def __delete__(self, obj):
#         self.val=None

class RecursionGuard:
    """  用于防止递归  """
    _box = set()

    def __init__(self, obj):
        """  obj 作为标识的对象  """
        self.obj = obj

    @classmethod
    def guard(cls, obj):
        cls._box.add(obj)

    @classmethod
    def release(cls, obj):
        cls._box.discard(obj)

    @classmethod
    def has(cls, obj):
        return obj in cls._box

    def __enter__(self):
        self.guard(self.obj)
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.release(self.obj)

def deepUpdate(origin:MutableMapping, new:Mapping):
    """  递归地用 new 更新 origin  """
    origin = copy.copy(origin)
    for k,n in new.items():
        if (o := origin.get(k, Undefined)) is not Undefined and isinstance(o, MutableMapping) and isinstance(n, Mapping):
            origin[k] = deepUpdate(o, n)
        else:
            origin[k] = n
    return origin

# def deepIntersect(origin:MutableMapping, new:Mapping):
#     """  递归地用 new 更新 origin，只更新 origin 中已有项  """
#     for k,o in origin.items():
#         if (n := new.get(k, Undefined)) is Undefined:
#             continue
#         if isinstance(o, MutableMapping) and isinstance(n, Mapping):
#             deepIntersect(o, n)
#         else:
#             origin[k] = n
#     return origin

import sys
import types
import functools
from typing import ForwardRef, _eval_type, TYPE_CHECKING

if TYPE_CHECKING:
    def _eval_type(t, globalns, localns, recursive_guard=frozenset()) -> type:
        pass

# import typing
# _eval_type:Callable = typing.__dict__["_eval_type"]

# 拷贝自 inspect.py，稍作修改
def get_annotations(obj, *, globals=None, locals=None, eval_str=False):
    """Compute the annotations dict for an object.

    obj may be a callable, class, or module.
    Passing in an object of any other type raises TypeError.

    Returns a dict.  get_annotations() returns a new dict every time
    it's called; calling it twice on the same object will return two
    different but equivalent dicts.

    This function handles several details for you:

      * If eval_str is true, values of type str will
        be un-stringized using eval().  This is intended
        for use with stringized annotations
        ("from __future__ import annotations").
      * If obj doesn't have an annotations dict, returns an
        empty dict.  (Functions and methods always have an
        annotations dict; classes, modules, and other types of
        callables may not.)
      * Ignores inherited annotations on classes.  If a class
        doesn't have its own annotations dict, returns an empty dict.
      * All accesses to object members and dict values are done
        using getattr() and dict.get() for safety.
      * Always, always, always returns a freshly-created dict.

    eval_str controls whether or not values of type str are replaced
    with the result of calling eval() on those values:

      * If eval_str is true, eval() is called on values of type str.
      * If eval_str is false (the default), values of type str are unchanged.

    globals and locals are passed in to eval(); see the documentation
    for eval() for more information.  If either globals or locals is
    None, this function may replace that value with a context-specific
    default, contingent on type(obj):

      * If obj is a module, globals defaults to obj.__dict__.
      * If obj is a class, globals defaults to
        sys.modules[obj.__module__].__dict__ and locals
        defaults to the obj class namespace.
      * If obj is a callable, globals defaults to obj.__globals__,
        although if obj is a wrapped function (using
        functools.update_wrapper()) it is first unwrapped.
    """
    if isinstance(obj, type):
        # class
        obj_dict = getattr(obj, '__dict__', None)
        if obj_dict and hasattr(obj_dict, 'get'):
            ann = obj_dict.get('__annotations__', None)
            if isinstance(ann, types.GetSetDescriptorType):
                ann = None
        else:
            ann = None

        obj_globals = None
        module_name = getattr(obj, '__module__', None)
        if module_name:
            module = sys.modules.get(module_name, None)
            if module:
                obj_globals = getattr(module, '__dict__', None)
        obj_locals = dict(vars(obj))
        unwrap = obj
        
        # 用于在 _get_annotations 中创建 ForwardRef
        is_argument=False
        is_class=True

    elif isinstance(obj, types.ModuleType):
        # module
        ann = getattr(obj, '__annotations__', None)
        obj_globals = getattr(obj, '__dict__')
        obj_locals = None
        unwrap = None

        # 用于在 _get_annotations 中创建 ForwardRef
        is_argument=False
        is_class=False

    elif callable(obj):
        # this includes types.Function, types.BuiltinFunctionType,
        # types.BuiltinMethodType, functools.partial, functools.singledispatch,
        # "class funclike" from Lib/test/test_inspect... on and on it goes.
        ann = getattr(obj, '__annotations__', None)
        obj_globals = getattr(obj, '__globals__', None)
        obj_locals = None
        unwrap = obj

        # 用于在 _get_annotations 中创建 ForwardRef
        is_argument=True
        is_class=False

    else:
        raise TypeError(f"{obj!r} is not a module, class, or callable.")

    if ann is None:
        return {}

    if not isinstance(ann, dict):
        raise ValueError(f"{obj!r}.__annotations__ is neither a dict nor None")

    if not ann:
        return {}

    if not eval_str:
        return dict(ann)

    if unwrap is not None:
        while True:
            if hasattr(unwrap, '__wrapped__'):
                unwrap = unwrap.__wrapped__
                continue
            if isinstance(unwrap, functools.partial):
                unwrap = unwrap.func
                continue
            break
        if hasattr(unwrap, "__globals__"):
            obj_globals = unwrap.__globals__

    if globals is None:
        globals = obj_globals
    if locals is None:
        locals = obj_locals
    # 如果 locals 有内容，与 obj_locals 合并
    elif isinstance(locals,MutableMapping):
        # locals.update(obj_locals)  # 这样可能会修改默认的 local
        locals = { **locals, **obj_locals }  
    # return_value = {key:
    #     value if not isinstance(value, str) else eval(value, globals, locals)
    #     for key, value in ann.items() }

    # 换成 _get_annotations，用 typing 中的 _eval_type 处理 ForwardRef
    return dict(_get_annotations(ann, globals, locals, is_argument, is_class))

# 借鉴了 typing.get_type_hints 的处理
def _get_annotations(ann:dict[str], globals, locals, is_argument=False, is_class=True):
    for key, value in ann.items():
        if value is None:
            value = type(None)
        elif isinstance(value, str):
            value = ForwardRef(value, is_argument=is_argument, is_class=is_class)
        value = getattr(value,"__mimic__",value)  # ConfigMeta 处理过的类变成新类
        yield key, _eval_type(value, globals, locals)

if __name__ == "__main__":

    from repiko.core.log import logger

    logger.debug(_eval_type)
    
    from typing import TypedDict, Literal

    class InnerTD(TypedDict):
        x:int
        y:int
        z:str

    class TDCFG(TypedDict):

        a:int
        b:str
        c:set
        d:list
        e:dict
        f:Literal["literal"]
        g:float | str
        inner:InnerTD
        inner2:InnerTD
        nested:TDCFG

    logger.debug(get_annotations(TDCFG,eval_str=True))

    def f():
        return inspect.currentframe().f_back # 返回调用 f 的 frame

    def test4():

        fr=f()
        logger.debug(fr.f_locals) # 这里还没有 Test4，但定义、返回后就有了

        class Test4:
            x:int
            y:float
            inner:Test4
            it="good"

        # logger.debug(get_annotations(Test4,eval_str=True))

        return Test4, fr

    t4, frame=test4()

    logger.debug(frame.f_locals) # 这里包含了 Test4

    logger.debug(get_annotations(t4, locals=frame.f_locals, eval_str=True))

    def test44():

        Int=int

        def test4():
            Int  # 不引入就会报错
            class Test4:
                x:Int
                y:float
                inner:Test4
                it="good"
            return Test4, f()
        return test4

    t4, frame=test44()()

    logger.debug(frame.f_locals)

    logger.debug(get_annotations(t4, locals=dict(frame.f_locals), eval_str=True))
