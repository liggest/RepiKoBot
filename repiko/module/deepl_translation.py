
from __future__ import annotations

from deepl.translator import Translator,Formality
from deepl import DeepLException

from enum import Enum

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Self

def removeTail(s:str,tail:str):
    """ s 尾部有 tail 则移除并返回，无则返回 None """
    if s.endswith(tail):
        return s.removesuffix(tail)

class DeepTrans:

    class Lang(str,Enum):
        保加利亚 = "BG"
        捷克 = "CS"
        丹麦 = "DA"
        德 = "DE"
        希腊 = "EL"

        英 = "EN"
        美式英 = "EN-US"
        # 美国英 = "EN-US"
        英式英 = "EN-GB"
        # 英国英 = "EN-GB"

        西班牙 = "ES"
        西 = "ES"   # ~

        爱沙尼亚 = "ET"
        芬兰 = "FI"
        法 = "FR"
        匈牙利 = "HU"
        印度尼西亚 = "ID"
        印尼 = "ID"
        意大利 = "IT"
        # 意 = "IT"
        日 = "JA"
        日本 = "JA"
        立陶宛 = "LT"
        拉脱维亚 = "LV"
        荷兰 = "NL"
        波兰 = "PL"

        葡萄牙 = "PT"
        葡 = "PT"   # ~
        葡萄牙葡萄牙 = "PT-PT"
        葡萄牙葡 = "PT-PT"
        巴西葡萄牙 = "PT-BR"
        巴西葡 = "PT-BR"

        罗马尼亚 = "RO"
        俄 = "RU"
        斯洛伐克 = "SK"
        斯洛文尼亚 = "SL"
        瑞典 = "SV"
        土耳其 = "TR"
        乌克兰 = "UK"
        中 = "ZH"
        汉 = "ZH"
        
        @classmethod
        def get(cls,name:str) -> Self|None:
            return cls._member_map_.get(name)

        @classmethod
        def fromName(cls,name:str) -> Self|None:
            if lang:=cls.get(name):
                return lang
            if temp:=removeTail(name,"语"):
                if temp != "中" and (lang:=cls.get(temp)): # no 中语
                    return lang
            elif temp:=removeTail(name,"文"):
                if temp != "日本" and (lang:=cls.get(temp)): # no 日本文
                    return lang
            elif temp:=removeTail(name,"国话"): # 如 英国话  英式英国话
                if temp=="英":
                    return cls.英式英 # 英国话 => 英式英语
                if temp=="美":
                    return cls.美式英
                con=(len(temp)==1 and temp not in { "西","日","汉" }) or temp in { "英式英","美式英","巴西葡","巴西葡" }
                if con and (lang:=cls.get(temp)):    # no 汉国话
                    return lang
            elif temp:=removeTail(name,"话"): # 如 瑞典话
                con=len(temp)>1 and temp not in { "英式英","美式英","巴西葡","巴西葡" } # no 英式英话
                if con and (lang:=cls.get(temp)):
                    return lang

        @classmethod
        def fromCode(cls,code:str):
            return cls(code.upper())

        @classmethod
        def fromStr(cls,s:str) -> Self:
            return cls.fromName(s) or cls.fromCode(s)

        @property
        def langName(self):
            if self==DeepTrans.Lang.中:
                return "中文"
            return f"{self.name}语" # 葡 => 葡萄牙语

        def unregion(self):
            """  EN-US => EN  PT-PT => PT ...  """
            return self.fromCode(self.split("-")[0])
    
    @staticmethod
    def code(lang:Lang|None):
        """ lang 的语言码或 None """
        if lang:
            return lang.value

    @classmethod
    def addRegion(cls,lang:Lang):
        """  EN => EN-US  PT=>PT-PT  """
        return { 
            cls.Lang.英 : cls.Lang.美式英, 
            cls.Lang.葡萄牙 : cls.Lang.葡萄牙葡萄牙 
        }.get(lang,lang) # 默认返回自己

    @staticmethod
    def noRegion(lang:Lang,remove:bool):
        return lang.unregion() if remove else lang

    @staticmethod
    def errorLan(e:ValueError):
        msg="".join(e.args)
        ridx=msg.rfind("is not")
        return msg[:ridx].strip().strip("'")

    FirstLang =Lang.中 # 默认翻译到中文
    SecondLang=Lang.英 # 默认从中文翻译到英文

    def __init__(self):
        self.translator:Translator=None

    def init(self,key):
        self.translator=Translator(key)

    def translate(self,text:str,fromLan:str|None=None,toLan:str=None,formality=None):
        try:
            regioned=False
            if toLan:
                old=self.Lang.fromStr(toLan)
                toLan=self.addRegion(old)
                regioned=old!=toLan # toLan 被规范化，加入了区域
            else:
                toLan=self.FirstLang # 默认翻译到 FirstLang
            if fromLan is not None: # 默认为 None
                fromLan=self.Lang.fromStr(fromLan).unregion()
        except ValueError as e:
            # print(e)
            return [f"不认识叫“{self.errorLan(e)}”的语言…"]
        
        result=[]
        try:
            trans=self.translator.translate_text(text,source_lang=self.code(fromLan),target_lang=self.code(toLan),formality=formality)
            detectLan=self.Lang.fromCode(trans.detected_source_lang)
            if fromLan is None and detectLan==toLan==self.FirstLang: # FirstLang 撞车，翻译到 SecondLang
                return self.translate(text,fromLan=detectLan,toLan=self.SecondLang,formality=formality)
            fromLan=detectLan
            result.append(f"尝试：{fromLan.langName}→{self.noRegion(toLan,regioned).langName}…")
            # 除非故意将 toLan 设定为 美式英语 等带区域的语言，否则显示时忽略 toLan 的区域信息
            result.append(trans.text)
        except (DeepLException,ValueError,TypeError) as e:
            # print(e)
            result.append(f"尝试：未知语言→{toLan.langName}…")
            result.append("结果什么都没翻译出来嘛！")
        
        return result
        
if __name__=="__main__":
    a=DeepTrans()
    # a.init(...)
    # print(a.translate("ありがとうございます!"))
    # print(a.translate("Nice to meet you..."))
    # print(a.translate("Nice to meet you...",fromLan="英式英文"))
    # print(a.translate("好啊"))
    # print(a.translate("好啊",fromLan="中文",toLan="汉语"))
    # print(a.translate("你好",toLan="葡萄牙话"))
    # print(a.translate("お疲れ様です!",fromLan="ZH"))
    # print(a.translate("お疲れ様です!",fromLan="ZH",toLan="英国话"))
    # print(a.translate("无可奉告",toLan="日国话"))
    # print(a.translate("中心",toLan="英国话"))
    # print(a.translate("中心",toLan="美国话"))
