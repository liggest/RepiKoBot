import functools

class MessageMeta(type):

    # clsNames={ c.__name__:c for c in (int,float,complex,str,bool,list,tuple,dict,set)}
    # 基础类型，名称索引 如 'str':str
    # 不验证类型的话，就不用这个了吧

    @classmethod
    def __prepare__(meta,name:str,bases:tuple,**kw) -> dict:
        members=super().__prepare__(name,bases,**kw)
        return members

    def __new__(meta,name:str,bases:tuple,members:dict[str],**kw):
        if bases: 
            _data=[] # 记录各类中定义的字段名称
            if bases[0] is dict:
                meta.base_annotations=members.get("__annotations__",{}) # 记录父类的标注信息
                # print("base",meta.base_annotations)
            else: # 并非dict的直接子类
                # print("name",name)
                defaults={}
                for k,v in members.get("__annotations__",{}).items(): # 只考虑有类型标注的字段
                    if k in meta.base_annotations:
                        continue  # 不管父类中存在的字段，只要子类新定义的
                    # if isinstance(v,str) and v in meta.clsNames:
                    #     v=meta.clsNames[v] # 'str' => str
                    # 把 k 定义成属性
                    if k in members:
                        defaults[k]=members[k] # 记录 k 字段的默认值
                    members[k]=meta.keyAsProperty(k,v)
                    _data.append(k)
                if defaults: # 如果有存在默认值的字段，修改 __init__
                    preinit=members.get("__init__")
                    # print(preinit)
                    def __init__(self,*iargs,**ikw):
                        if preinit:
                            preinit(self,*iargs,**ikw) # 执行默认的 __init__

                        for k,v in defaults.items():   # 在 __init__ 中额外为属性设置默认值
                            if getattr(self,k,None) is None:
                                setattr(self,k,v)
                    members["__init__"]=functools.wraps(preinit)(__init__) if preinit else __init__
            members["_data"]=tuple(_data)

        # return 
        # print(name,{k:v for k,v in members.items() if not k.endswith("__") })
        # print(members.get("__annotations__",{}))
        # print("="*40)
        # print(inspect.get_annotations(obj,eval_str=True))
        return super().__new__(meta,name,bases,members,**kw)

    @staticmethod
    def keyAsProperty(key:str,mark:type|str):
        def kget(self):
            return self["data"].get(key)
        def kset(self,val):
            self["data"][key]=val
        def kdel(self):
            del self["data"][key]
        kget.__annotations__.update({"return":mark}) # 例 v=str  kget(self) -> str
        kset.__annotations__.update({"val":mark})    # 例 v=str  kset(self,val:str)
        return property(kget,kset,kdel,f'self["data"]["{key}"]\n\n不存在时返回 None')

