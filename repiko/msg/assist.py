from typing import Iterable, Text

from LSparser.command import ParserCore,ParseResult

from repiko.msg.part import At, MessagePart,Text
from repiko.msg.content import Content
from repiko.msg.data import Message

# class TupleStr(tuple):

#     def __new__(cls,val):
#         if isinstance(val,str): # 只是字符串的话就好好当字符串啊！
#             return val
#         elif not isinstance(val,Iterable):
#             val=(val,)
#         return super().__new__(cls,val)

#     def __str__(self): 
#         return "".join(str(v) for v in super().__iter__())

#     def __repr__(self): 
#         content=''.join(v if isinstance(v,str) else repr(v) for v in super().__iter__())
#         return f"{self.__class__.__name__}('{content}')"

#     # def __eq__(self, other):
#     #     if isinstance(other, str):
#     #         return str(self) == other
#     #     return super().__eq__(other)

#     def __contains__(self, other):
#         if isinstance(other, str):
#             for val in super().__iter__():
#                 if isinstance(val,str) and other in val:
#                     return True
#         return super().__contains__(other)

#     def __iter__(self):
#         for val in super().__iter__():
#             if isinstance(val,str):
#                 yield from val
#             else:
#                 yield self.__class__(val)

#     def startswith(self,prefix):
#         for a,b in zip(self,prefix):
#             if a!=b:
#                 return False
#         return True

#     @staticmethod
#     def _lstrip(iter,chars=None):
#         stripped=False
#         for val in iter:
#             if stripped:
#                 yield val
#             else:
#                 if isinstance(val,str):
#                     newVal=val.lstrip(chars)
#                     if newVal:
#                         stripped=True
#                         yield newVal
#                 else:
#                     if not chars or val==chars or (isinstance(chars,Iterable) and val in chars):
#                         stripped=True
#                         yield val

#     def lstrip(self,chars=None): 
#         return self.__class__(self._lstrip(super().__iter__(),chars))

#     def rstrip(self,chars=None):
#         return self.__class__(
#             reversed(
#                 self._lstrip(reversed(super().__iter__()),chars)
#             )
#         )

#     def strip(self,chars=None):
#         return self.__class__(
#             reversed(
#                 self._lstrip(
#                     reversed(self._lstrip(super().__iter__(),chars))
#                 ,chars)
#             )
#         )

class CustomParser(ParserCore):

    @classmethod
    def getCommand(cls,t,pr,parser):
        if isinstance(t,Message):
            if t.isReply:
                pr=cls.getCommandStr(str(t.noReplyContent),pr,parser) # 除去 Reply
            else:
                pr=cls.getCommandStr(str(t),pr,parser)
            # print(pr._cons)
        else:
            pr=super().getCommand(t,pr,parser)
        return pr

    @classmethod
    def isCommand(cls,t,cp):
        pr=ParseResult(parser=cp)
        pr=cls.getCommand(t,pr,cp)
        return pr.isCommand()

    # @staticmethod
    # def tryYieldCurrent(current:list,strEnd=True):
    #     if current:
    #         if isinstance(current[-1],str) or (not strEnd):
    #             if len(current)==1 and isinstance(current[-1],str):
    #                 yield current[-1]
    #             else:
    #                 yield TupleStr(current)
    #             current.clear()

    # @classmethod
    # def tokenizeIter(cls,t:Iterable):
    #     current=[]
    #     for val in t:
    #         if isinstance(val,Text):
    #             val=val.text
    #         if isinstance(val,str):
    #             if not val:
    #                 continue
    #             strs=[*cls.tokenizeStr(val)]
    #             if val[0].isspace():
    #                 yield from cls.tryYieldCurrent(current,strEnd=False)
    #                 if not strs:
    #                     continue
    #             else:
    #                 yield from cls.tryYieldCurrent(current)
    #             current.append(strs.pop(0))
    #             if strs:
    #                 yield from cls.tryYieldCurrent(current)
    #                 last=strs.pop()
    #                 if strs:
    #                     yield from strs
    #                 current.append(last)
    #             if val[-1].isspace():
    #                 yield from cls.tryYieldCurrent(current,strEnd=False)
    #         else:
    #             current.append(val)
    #     yield from cls.tryYieldCurrent(current,strEnd=False)