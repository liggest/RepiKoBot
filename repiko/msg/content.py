from __future__ import annotations

from collections import defaultdict
from itertools import zip_longest
from typing import Type,List,Dict,Iterable

from repiko.msg.part import MessagePart,Text
from repiko.msg.util import isCQcode

class Content(list[MessagePart]):
    """ 消息内容 """

    @classmethod
    def asParts(cls,parts):
        """ 迭代 parts 中的元素，逐个输出 MessagePart 对象 """
        # if isinstance(parts,str) and "[CQ:" in parts:
        if isCQcode(parts):
            yield from cls.fromCQ(parts)
        elif MessagePart.isPart(parts):
            yield MessagePart.asPart(parts)
        elif isinstance(parts,Iterable):
            # 非字符串、非字典的可迭代对象
            for part in parts:
                # 也能处理嵌套列表
                yield from cls.asParts(part)
    
    @classmethod
    def fromCQ(cls,CQStr:str):
        parsed=0
        l=len(CQStr)
        while parsed<l:
            idx=CQStr.find("[CQ:",parsed)
            if idx>=0:
                if parsed<idx:
                    yield MessagePart.fromCQcode(CQStr[parsed:idx]) # 文本
                    parsed=idx
                eidx=CQStr.find("]",parsed+4)
                if eidx>=0:
                    yield MessagePart.fromCQcode(CQStr[idx:eidx+1])
                    parsed=eidx+1
                else:
                    raise ValueError("不完整的CQ码片段",CQStr)
            else:
                yield MessagePart.fromCQcode(CQStr[parsed:])  # 文本
                parsed=l

    def __init__(self,*args):
        """ 消息内容 """
        # cast= "cast" in kw and kw.pop("cast") # 如果有cast关键字参数，不执行 parts 的初始化

        # if len(args)>1 or (len(args)==1 and isinstance(args[0],str)):
        #     # Content(part1,part2,...)
        #     # Content("...")
        #     super().__init__(args,**kw)
        # # Content([part1,part2,...])
        # super().__init__(*args,**kw)
        super().__init__(self.asParts(args)) # 所有 args 都转为 MessagePart

        self._parts:Dict[str,list]=None   # 按类型记录消息段对象
        # self.parts=defaultdict(list) # 记录各消息段类型的对象们的下标
        # self._partsUpdate=set()
        # if not cast:
        #     for i,part in enumerate(self):
        #         part=MessagePart.asPart(part)
        #         self[i]=part
        #         self._addPart(part,i) # 默认传入的都是 MessagePart

    def __str__(self) -> str:
        return self.CQcode

    def __repr__(self) -> str:
        return self.__class__.__name__+super().__repr__() # Content[Text("..."), Face(123), ...]

    def __contains__(self,val) -> bool:
        """ 
            支持 \n
                Text in Content() \n
                "text" in Content() \n
                Text("...") in Content()
        """
        if self._hasPart(val): # 支持诸如 Text in Content()
            return True
        elif isinstance(val,MessagePart) and self._hasPart(type(val)):
            return val in self.parts[val.partType]
        elif isinstance(val,str) and self._hasPart(Text): # 支持判断字符串是否在消息中 "text" in Content()
            part:Text
            for part in self.parts[Text.partType]:
                if val in part.text:
                    return True
        return super().__contains__(val) # Text("...") in Content()

    def __getitem__(self,idx):
        """ 
            支持 \n
                Content()[Text] \n
                Content()[Text,::] \n
                Content()[::]
        """
        typeIdx=None
        if isinstance(idx,tuple): # [Text,::]
            idx,typeIdx=idx
        if self._hasPart(idx):
            idx:Type[MessagePart]
            if typeIdx is None:         # 支持 Content()[Text]
                return self.parts[idx.partType]
            else:                       # 支持 Content()[Text,::]
                return self.parts[idx.partType][typeIdx]
        elif isinstance(idx,type):
            raise IndexError(f"{repr(self)} 中不存在 {idx} 类型的对象")
        return super().__getitem__(idx) # 支持 Content()[::]
        # result=None
        # if isinstance(idx,slice) and self._hasPart(idx.start):
        #     if idx.stop is None: # self[Text] 得到全部Text
        #         result=[super().__getitem__(i) for i in self.parts[idx.start.partType]]
        #     elif idx.step is None: # self[Text:2] 得到全部Text中下标为2的 Text
        #         result=super().__getitem__(self.parts[idx.start.partType][idx.stop])
        #     else:   # self[Text:2:5] 得到下标由2到5的 Text
        #         result=[super().__getitem__(i) for i in self.parts[idx.start.partType][idx.stop:idx.step] ]
        # if result is None:
        #     result=super().__getitem__(idx)
        # if type(result) is list:
        #     result=self.__class__(result)
        # return result

    def __setitem__(self,idx,val):
        """ 
            支持 \n
                Content()[Text]=[...] \n
                Content()[Text,::]=[...] \n
                Content()[::]=[...] \n
            会重置 parts \n
            因为用了 zip，前两种情况的切片长度和赋值列表长度不等时，只处理其中较短者长度的量，要像列表默认行为那样太麻烦了
        """
        typeIdx=None
        if isinstance(idx,tuple):
            idx,typeIdx=idx
        valRaw=val
        val=[*self.asParts(val)] # MessagePart对象构成的列表
        if self._hasPart(idx):
            idx:Type[MessagePart]
            toDel=None
            if typeIdx is None:         # 支持 Content()[Text]=[...]
                gen=( i for i,part in enumerate(self) if isinstance(part,idx) ) # 所有idx类别的消息片段的下标
                lasti=-1
                for i,newPart in zip_longest(gen,val):
                    # print(i,newPart)
                    if newPart is None:
                        toDel=[i,*gen]
                        break
                    if i is None:
                        lasti+=1
                        super().insert(lasti,newPart)
                    else:
                        super().__setitem__(i,newPart) # self[i] 替换为 val 中的新值
                        lasti=i
            else:                       # 支持 Content()[Text,::]=[...]
                old=self.parts[idx.partType][typeIdx]
                if isinstance(old,MessagePart): # 单个元素变成列表
                    old=[old]
                i=0
                toDel=[]
                for oldPart,newPart in zip_longest(old,val):
                    if oldPart is not None:
                        while not (self[i] is oldPart):
                            i+=1
                        if newPart is None:
                            toDel.append(i)
                        else:
                            super().__setitem__(i,newPart)
                    else:
                        i+=1
                        super().insert(i,newPart)
            if toDel:
                for i in reversed(toDel):
                    # print("del",i)
                    super().__delitem__(i)
        # if isinstance(idx,slice) and self._hasPart(idx.start):
        #     if not idx.stop:    # self[Text]=[...] 替换全部 Text
        #         [super().__setitem__(i,v) for i,v in zip(self.parts[idx.start.partType],val)]
        #     elif not idx.step:  # self[Text:2]=Text 得到全部Text中下标为2的 Text
        #         super().__setitem__(self.parts[idx.start.partType][idx.stop],val)
        #     else:               # self[Text:2:5]=[...] 替换下标由2到5的 Text
        #         [super().__setitem__(i,v) for i,v in zip(self.parts[idx.start.partType][idx.stop:idx.step],val)]
        #     return
        elif isinstance(idx,type):
            raise IndexError(f"{repr(self)} 中不存在 {idx} 类型的对象")
        else:
            super().__setitem__(idx,valRaw) # 支持 Content()[::]=[...]
        del self.parts # 因为列表刷新了，重置 parts
    
    def __delitem__(self,idx):
        """ 
            支持 \n
            del Content()[Text] \n
            del Content()[Text,::] \n
            del Content()[::] \n
        """
        typeIdx=None
        if isinstance(idx,tuple):
            idx,typeIdx=idx
        if self._hasPart(idx):
            idx:Type[MessagePart]
            if typeIdx is None:         # 支持 del Content()[Text]
                del self.parts[idx.partType]
                toDel=[i for i,part in enumerate(self) if isinstance(part,idx)] # 所有idx类别的消息片段的下标
                for i in reversed(toDel):   # 从下标最大的开始删 保证删除后前面待删的项下标不变
                    super().__delitem__(i)
            else:                       # 支持 del Content()[Text,::]
                typedParts=self.parts[idx.partType]
                old=typedParts[typeIdx]
                if isinstance(old,MessagePart): # 单个元素变成列表
                    old=[old]
                oldIdx=0
                toDel=[]
                for i,part in enumerate(self):
                    if part is old[oldIdx]:
                        toDel.insert(0,i) # 下标最大的在列表最前面
                        oldIdx+=1
                for i in toDel:    # 从下标最大的开始删
                    super().__delitem__(i)
                    # del typedParts[oldi]
                del typedParts[typeIdx]
                if not typedParts:
                    del self.parts[idx.partType]
        # if isinstance(idx,slice) and self._hasPart(idx.start):
        #     if not idx.stop:    # del self[Text] 删除全部 Text
        #         self.remove(idx.start)
        #     elif not idx.step:  # del self[Text:2] 删除得到全部Text中下标为2的 Text
        #         self.pop(idx.stop,idx.start)
        #     else:               # del self[Text:2:5] 删除下标由2到5的 Text
        #         parts=self.parts[idx.start.partType]
        #         for i in parts[idx.stop,idx.step]:
        #             self.pop(i)
        #         del parts[idx.stop,idx.step]
        #         if not parts:
        #             self.parts.pop(idx.start.partType)
        #         self._reinitPart()
        #     return
        elif isinstance(idx,type):
            raise IndexError(f"{repr(self)} 中不存在 {idx} 类型的对象")
        else:
            part=super().__getitem__(idx)
            if isinstance(idx,int):
                part:MessagePart
                typedParts=self.parts[part.partType]
                oldi=0
                while not (typedParts[oldi] is part):
                    oldi+=1
                del typedParts[oldi]
                if not typedParts:
                    del self.parts[part.partType]
            else:
                oldIdx=defaultdict( lambda x: enumerate(self.parts[x]) ) 
                # 用于缓存对特定种类消息片段的迭代状态
                # 初始为未迭代 enumerate(self.parts[p.partType])
                p:MessagePart
                toDel=[]
                for p in part:
                    ptype=p.partType
                    gen=oldIdx[ptype]
                    for oldi,old in gen:
                        if old is p:
                            toDel.insert(0,(ptype,oldi))
                            break
                    oldIdx[ptype]=gen # 存储迭代状态
                for ptype,oldi in toDel:
                    del self.parts[ptype][oldi]
                if not self.parts[ptype]:
                    del self.parts[ptype]
            super().__delitem__(idx)

    def __add__(self,other) -> Content:
        return self.__class__(super().__add__(other))

    def __radd__(self,other) -> Content:
        return self.__class__(other).__add__(self)
        
    def __iadd__(self,other) -> Content:
        if isinstance(other,MessagePart):
            other=[other]   # 不知道为什么可以 list += dict ...
        return self.__class__(super().__iadd__(other))

    def __mul__(self, n) -> Content:
        return self.__class__(super().__mul__(n))
    
    __rmul__ = __mul__

    def __imul__(self, n) -> Content:
        return self.__class__(super().__imul__(n))

    @property
    def CQcode(self:List[MessagePart]):
        """ CQ码形式的消息 """
        return "".join(part.CQcode for part in self) # 文本消息（CQ码已转义）

    @property
    def brief(self:List[MessagePart]):
        """ 简短文本消息 """
        return "".join(part.brief for part in self) # 文本消息（CQ码已转义）

    @property
    def parts(self):
        """ 按类型名称记录消息片段 """
        if self._parts is None: # 生成 parts
            self._parts=defaultdict(list) 
            for part in self:
                self._addPart(part)
        return self._parts

    @property
    def plainText(self):
        if self._hasPart(Text):
            return "".join(str(part) for part in self.parts[Text.partType])
        return ""

    @parts.deleter
    def parts(self): # 重置 parts
        self._parts=None

    def _hasPart(self,val:Type[MessagePart]) -> bool:
        """ 存在 val 类型的消息片段 """
        return isinstance(val,type) and val.partType in self.parts

    def _addPart(self,part:MessagePart):
        self._parts[part.partType].append(part)

    # def _updatePart(self,all=False):
    #     if all:
    #         self._partsUpdate=self._partsUpdate.union(self.parts.keys())
    #     for name in self._partsUpdate:
    #         self.parts.pop(name)
    #     for i,part in enumerate(self):
    #         part:MessagePart
    #         if part.partType in self._partsUpdate:
    #             self._addPart(part,i)
    #     self._partsUpdate.clear()

    # def _reinitPart(self):
    #     """ 重新生成 parts """
    #     self.parts.clear()
    #     for i,part in enumerate(self):
    #         self._addPart(part,i)

    # def _updatePart(self,opt:Union[int,callable]):
    #     """ 对 parts 中记录的下标做给定操作 """
    #     if isinstance(opt,int):
    #         optval=opt
    #         opt=lambda x:x+optval
    #     for name in self.parts:
    #         oldParts=self.parts[name]
    #         self.parts[name]=[opt(i) for i in oldParts]

    def append(self,part):
        part=MessagePart.asPart(part)
        # idx=len(self)
        super().append(part)
        # self._addPart(part,idx)
        if self._parts:
            self._addPart(part)

    def clear(self):
        super().clear()
        del self.parts
        # self.parts.clear()
        # self._partsUpdate.clear()

    def _copy(self):
        part:MessagePart
        for part in self:
            yield part.copy()

    def copy(self):
        """ 拷贝每个消息片段 """
        # dup=self.__class__(super().copy(),cast=True) # 不初始化 parts
        # for name,parts in self.parts.items():
        #     dup.parts[name]=parts.copy()
        # return dup
        return self.__class__(self._copy()) # 保证拷贝每个消息片段

    def count(self,val:MessagePart) -> int:
        """ 
            统计 val 的出现次数\n
                count(Text) 列表中的 Text 对象数量
        """
        if self._hasPart(val):
            return len(self.parts[val.partType]) # count(Text) => Text对象的数量
        return super().count(val)

    def extend(self,parts):
        idx=len(self)
        super().extend(self.asParts(parts))
        if self._parts:
            for part in self[idx:]: # 将新元素加入 parts
                self._addPart(part)
        # for i in range(idx,len(self)): # 将新元素加入 parts
        #     part=MessagePart.asPart(self[i])
        #     self[i]=part
        #     self._addPart(part,i)
    
    def index(self,val:MessagePart,start=0,stop=None) -> int:
        """
            寻找 val 在列表中的第一个下标 \n
                index(Text) 寻找第一个 Text 的下标\n
        """
        stop=stop if not stop is None else len(self)
        if self._hasPart(val):
            val=self.parts[val.partType][0] # 寻找第一个 val 类型的
            # if parts[0]<stop and parts[-1]>=start:
            #     for i in parts:
            #         if start<=i<stop:
            #             return i
        elif isinstance(val,str):
            for i,part in enumerate(self[start:stop]):
                if isinstance(part,Text) and val in part.text: # 暂定为包含 val 的 Text 都可以找到
                    return i+start
        return super().index(val,start,stop)

    def insert(self,idx:int,part):
        part=MessagePart.asPart(part)
        super().insert(idx, part)
        partIdx=0
        p:MessagePart
        for p in self[:idx]:
            if part.partType==p.partType:
                partIdx+=1
        self.parts[part.partType].insert(partIdx,part) # 把插入的片段放入 parts 中合适位置
        # self._updatePart(lambda x: x+1 if x>=idx else x)  # 所有在插入片段后的片段下标+1
        # parts=self.parts[part.partType]
        # i=0
        # for i in parts:
        #     if i>idx:
        #         break
        # parts.insert(i,idx) # 把插入片段的下标放入 parts 中合适位置
        # for name in self.parts:
        #     oldParts=self.parts[name]
        #     if name!=part.partType:
        #         self.parts[name]=[i+1 if i>=idx else i for i in oldParts]
        #     else:
        #         newParts=[]
        #         inserted=False
        #         for i in oldParts:
        #             if i>=idx and not inserted:
        #                 newParts.append(idx)
        #             newParts.append( i+1 if i>=idx else i )
        #         self.parts[name]=newParts

    def pop(self,idx:int=-1,val:Type[MessagePart]=None) -> MessagePart:
        """
            移除 idx 下标的项，返回之 \n
                pop(Text) 弹出最后一个 Text \n
                pop(0,Text) 弹出第一个 Text \n
        """
        if self._hasPart(idx):  # pop(Text) 弹出最后一个 Text 对象
            val=idx
            idx=-1  # 相当于 pop(-1,Text)
        if val and self._hasPart(val):  # pop(-1,Text) 弹出最后一个 Text 对象
            parts=self.parts[val.partType]
            old=parts.pop(idx)  # 弹出的是第 idx 个该类型的消息片段
            if not parts:
                del self.parts[val.partType]
            for idx,p in enumerate(self): # 这里得到了这个片段在列表中真正的下标
                if old is p:
                    break
            return super().pop(idx)
        # self._updatePart(lambda x: x-1 if x>idx else x)  # 所有在弹出片段后的片段下标-1
        part:MessagePart=super().pop(idx)
        if self._parts:
            typedParts=self.parts[part.partType]
            oldi=0
            while not (typedParts[oldi] is part):
                oldi+=1
            typedParts.pop(oldi)
            if not typedParts:
                del self.parts[part.partType]
        return part

    def remove(self,val:MessagePart):
        # if self._hasPart(val):      # remove(Text) 移除所有 Text 对象
        #     del self[val]
        #     # del self.parts[val.partType]
        #     # parts=self.parts.pop(val.partType)
        #     # for i in parts[::-1]:
        #     #     self.pop(i)
        #     # self._reinitPart()
        # else:
        super().remove(val)
        if self._parts:
            typedParts=self.parts[val.partType]
            typedParts.remove(val)
            if not typedParts:
                del self.parts[val.partType]

    def removeAll(self,val:MessagePart) -> int:
        """
            移除所有 val，返回移除的个数\n
                remove(Text)，移除全体 Text
        """
        count=0
        if self._hasPart(val):      # remove(Text) 移除所有 Text 对象
            count=len(self.parts[val.partType])
            del self[val]
        elif isinstance(val,MessagePart) and self._hasPart(type(val)):
            newParts=[]
            for i in range(len(self)-1,-1,-1):
                part:MessagePart=self[i]
                if part==val:
                    super().pop(i)
                    count+=1
                elif val.partType==part.partType:
                    newParts.insert(0,part)
            if newParts:
                self.parts[val.partType]=newParts
            else:
                del self.parts[val.partType]
        return count

    def reverse(self):
        super().reverse()
        if self._parts:
            for parts in self.parts.values():
                parts.reverse()
        # l=len(self)-1
        # self._updatePart(lambda x: l-x) # 元素的下标 x 变为 l-x

    def sort(self):
        """ 
            对列表排序\n
            会重置 parts
        """
        super().sort()  # TODO 因为 MessagePart 间没法比较，暂时用不了
        del self.parts
        # self._reinitPart()

