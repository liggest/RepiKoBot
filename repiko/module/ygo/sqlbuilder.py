from ygo.constant import *

class SQLBuilder:

    _base="SELECT t.name,t.DESC,d.* FROM texts t INNER JOIN datas d ON t.id=d.id"
    _names=("keyword","race","attribute","cardType","level","rank","link","Pmark","attack","defence","id","atkDefSum","atkEqDef")

    def __init__(self):
        self.materials={}
        self.params=[]
        self.conditions=[]
        self.sql:str=self._base

    def __str__(self):
        return self.resolve()

    def __repr__(self) -> str:
        return self.materials.__repr__()+"\n"+super.__repr__()

    @staticmethod
    def _upperFirst(text:str):
        return text[:1].upper()+text[1:]

    @staticmethod
    def dealKeyword(text:str) -> str: # 占位 暂不处理
        return text

    @staticmethod
    def dealRace(text:str) -> CardRace:
        if text.endswith("族"):
            text=text[:-1]
        return str2cardRace.get(text)

    @staticmethod
    def dealAttribute(text:str) -> CardAttribute:
        if text.endswith("属性"):
            text=text[:-2]
        return str2cardAttribute.get(text)

    @staticmethod
    def dealCardType(text:str) -> CardType:
        if text.endswith("卡"):
            text=text[:-1]
        if (text.endswith("怪兽") and text!="怪兽") or (text.endswith("魔法") and text!="魔法") or (text.endswith("陷阱") and text!="陷阱"):
            text=text[:-2]
        return str2cardType.get(text)

    @staticmethod
    def _dealAD(text:str) -> int:
        if text.isdigit() and len(text)<5: # 4 位及以下的数
            return int(text)
        if text=="？" or text=="?":
            return -2

    @classmethod
    def dealAttack(cls,text:str) -> int:
        text=text.lower()
        for x in ("atk","攻击力","打点","攻击","攻"):
            if text.startswith(x):
                text=text[len(x):]
            if text.endswith(x):
                text=text[:-len(x)]
        return cls._dealAD(text)

    @classmethod
    def dealDefence(cls,text:str) -> int:
        text=text.lower()
        for x in ("def","守备力","防御力","防御","守备","守","防"):
            if text.startswith(x):
                text=text[len(x):]
            if text.endswith(x):
                text=text[:-len(x)]
        return cls._dealAD(text)

    @staticmethod
    def _dealADSum(text:str) -> int:
        if text.isdigit(): 
            val=int(text)
            if val<=10000: # 4 位及以下的数，以及特例 10000
                return val
        if text=="？" or text=="?":
            return -4

    @classmethod
    def dealAtkDefSum(cls,text:str) -> int:
        text=text.lower()
        for x in ("攻守和","攻防和","攻加守","攻加防","攻击加防御","攻击加守备","atk+def","攻守","攻防"):
            if text.startswith(x):
                text=text[len(x):]
            if text.endswith(x):
                text=text[:-len(x)]
        return cls._dealADSum(text)

    @staticmethod
    def _dealMark(text:str) -> int:
        if text.isdigit(): 
            val=int(text)
            if 0<val<15:    # 1-15 的数
                return val

    @classmethod
    def dealLevel(cls,text:str) -> int:
        text=text.lower()
        if text.startswith(("等级","lv")):
            text=text[2:]
        if text.startswith("l"):
            text=text[1:]
        if text.endswith("星"):
            text=text[:-1]
        return cls._dealMark(text)

    @classmethod
    def dealRank(cls,text:str) -> int:
        text=text.lower()
        if text.startswith("阶级"):
            text=text[2:]
        if text.startswith("r"):
            text=text[1:]
        if text.endswith("阶"):
            text=text[:-1]
        return cls._dealMark(text)

    @classmethod
    def dealLink(cls,text:str) -> int:
        text=text.lower()
        if text.startswith("link"):
            text=text[4:]
        if text.startswith(("连接","链接")):
            text=text[2:]
        return cls._dealMark(text)

    @classmethod
    def dealPmark(cls,text:str) -> int:
        text=text.lower()
        for x in ("灵摆","刻度","p"):
            if text.startswith(x):
                text=text[len(x):]
            if text.endswith(x):
                text=text[:-len(x)]
        return cls._dealMark(text)

    @staticmethod
    def dealId(text:str) -> int:
        # print(text)
        if text.isdigit() and len(text)>4: # 5 位及以上的数
            return int(text)

    def _addFlag(self,name:str,*args):
        items=self.materials.get(name)
        for i in args:
            if isinstance(i,str): #不是 str 的话就不会检查数据
                i=getattr(self,f"deal{self._upperFirst(name)}")(i) # name="race" => self.dealRace(i)
                # 用 str.capitalize 会导致其余字母都变小写 cardType => Cardtype
                if i is None:
                    continue
            if not items:
                items=i
            else:
                items|=i
        if items:
            self.materials[name]=items
            return True

    def _addToList(self,name:str,*args):
        items=self.materials.get(name,[])
        for i in args:
            if isinstance(i,str): #不是 str 的话就不会检查数据
                i=getattr(self,f"deal{self._upperFirst(name)}")(i) # name="keyword" => self.dealKeyword(i)
                if i is None:
                    continue
            items.append(i)
        if items:
            self.materials[name]=items
            return True

    def _resolveValue(self,name):
        val=self.materials.get(name)
        if not val and val!=0:
            return
        sqlfunc=getattr(self,f"_{name}SQL")
        if isinstance(val,list): # 多个可能的值
            valsql=" OR ".join(sqlfunc(v) for v in val)
            if len(val)>1:
                valsql=f"({valsql})"
        else:
            valsql=sqlfunc(val)
        self.conditions.append(valsql)

    def _resolveKeyword(self):
        kws=self.materials.get("keyword")
        if not kws:
            return
        hasOR=False
        for kw in kws:
            kwsql=self._keywordSQL(kw)
            # names=("race","attribute","cardType","attack","defence")
            exception=("keyword","atkEqDef")
            for name in (n for n in self._names if not n in exception):
                val=getattr(self,f"deal{self._upperFirst(name)}")(kw) # self.dealXxx
                if val is not None:
                    sqlfunc=getattr(self,f"_{name}SQL") # self._xxxSQL
                    kwsql=f"{kwsql} OR {sqlfunc(val)}"
                    hasOR=True
            if hasOR:
                kwsql=f"({kwsql})"
            self.conditions.append(kwsql)

    def _resolveRace(self):
        self._resolveValue("race")

    def _resolveAttribute(self):
        self._resolveValue("attribute")

    def _resolveCardType(self):
        self._resolveValue("cardType")

    def _resolveAttack(self):
        self._resolveValue("attack")

    def _resolveDefence(self):
        self._resolveValue("defence")

    def _resolveLevel(self):
        self._resolveValue("level")
    
    def _resolveRank(self):
        self._resolveValue("rank")

    def _resolveLink(self):
        self._resolveValue("link")

    def _resolvePmark(self):
        self._resolveValue("Pmark")

    def _resolveId(self):
        self._resolveValue("id")

    def _resolveAtkDefSum(self):
        self._resolveValue("atkDefSum")

    def _resolveAtkEqDef(self):
        if self.materials.get("atkEqDef"):
            self.conditions.append(self._atkEqDefSQL())

    def _checkHas(self,name,*args):
        item=self.materials.get(name)
        if not item:
            return False
        for x in args:
            if not x in item:
                return False
        return True

    def _ensureCardType(cardType:CardType):
        def deco(func):
            def wrapper(self:"SQLBuilder",*args):
                raw=func(self,*args)
                if self._checkHas("cardType",cardType):
                   return raw # 原 SQL 条件
                return f"({raw} AND {self._cardTypeSQL(cardType)})" # 附加上 CardType 条件
            return wrapper
        return deco

    def _keywordSQL(self,kw):
        self.params.append(f"%{kw}%")
        # return r"t.name ||'\n' || t.DESC LIKE '%?%'"
        return r"t.name ||'\n' || t.DESC LIKE ?"

    @_ensureCardType(CardType.Monster)
    def _raceSQL(self,race:CardRace):
        return f"d.race & {race.value}!=0"

    @_ensureCardType(CardType.Monster)
    def _attributeSQL(self,attribute:CardAttribute): # 满足一个属性的就算
        return f"d.attribute & {attribute.value}!=0"

    def _cardTypeSQL(self,cardType:CardType):
        return f"d.type & {cardType.value}={cardType.value}" # 满足所有种类的才算

    @_ensureCardType(CardType.Monster)
    def _attackSQL(self,attack):
        return f"d.atk={attack}"

    @_ensureCardType(CardType.Monster)
    def _defenceSQL(self,defence):
        return f"d.def={defence}"

    @_ensureCardType(CardType.Monster)
    def _levelSQL(self,level):
        return f"d.level & 15={level}" # 15->0b1111

    _rankSQL=_levelSQL
    _rankSQL=_ensureCardType(CardType.Xyz)(_rankSQL)

    _linkSQL=_levelSQL
    _linkSQL=_ensureCardType(CardType.Link)(_linkSQL)

    @_ensureCardType(CardType.Monster|CardType.Pendulum)
    def _PmarkSQL(self,Pmark):
        return f"( (d.level & 0xF000000)>>24 ={Pmark} OR (d.level & 0x00F0000)>>16 ={Pmark} )"

    def _idSQL(self,id):
        return f"d.id={id}"

    @_ensureCardType(CardType.Monster)
    def _atkDefSumSQL(self,atkDefSum):
        return f"d.atk+d.def={atkDefSum}"

    @_ensureCardType(CardType.Monster)
    def _atkEqDefSQL(self):
        return f"(d.atk=d.def AND d.atk!=-2 AND d.def!=-2)"
        # return f"d.atk=d.def"

    def keyword(self,*args):
        self._addToList("keyword",*args)
        return self

    name=keyword

    def race(self,*args):
        if self._addFlag("race",*args):
            self.cardType(CardType.Monster)
        return self

    def attribute(self,*args):
        if self._addFlag("attribute",*args):
            self.cardType(CardType.Monster)
        return self

    def cardType(self,*args):
        self._addFlag("cardType",*args)
        return self

    def attack(self,*args):
        if self._addToList("attack",*args):
            self.cardType(CardType.Monster)
        return self

    def defence(self,*args):
        if self._addToList("defence",*args):
            self.cardType(CardType.Monster)
        return self
    
    def level(self,*args):
        if self._addToList("level",*args):
            self.cardType(CardType.Monster)
        return self

    def rank(self,*args):
        if self._addToList("rank",*args):
            self.cardType(CardType.Monster,CardType.Xyz)
        return self

    def link(self,*args):
        if self._addToList("link",*args):
            self.cardType(CardType.Monster,CardType.Link)
        return self

    def Pmark(self,*args):
        if self._addToList("Pmark",*args):
            self.cardType(CardType.Monster,CardType.Pendulum)
        return self

    def id(self,*args):
        self._addToList("id",*args)
        return self

    def atkDefSum(self,*args):
        if self._addToList("atkDefSum",*args):
            self.cardType(CardType.Monster)
        return self

    def atkEqDef(self):
        self.materials["atkEqDef"]=True
        self.cardType(CardType.Monster)
        return self

    def resolve(self):
        self.conditions=[]
        self.params=[]
        # names=("keyword","race","attribute","cardType","attack","defence","id")
        for name in self._names:
            getattr(self,f"_resolve{self._upperFirst(name)}")() # self._resolveXxx()
        cons=" AND ".join(self.conditions)
        self.sql=f"{self._base} WHERE {cons}"
        return self.sql

if __name__ == "__main__":
    b=SQLBuilder()
    # b.name("混沌","光","战士族","600","5000").race("机械").cardType(CardType.Monster,CardType.Link,"魔法卡").attribute("炎属性")
    # b.attack(3000,"6900","99999").defence("19.3","?","3000").id("40","10000",5000).level("0星","10星","L6",13)
    # b.name("异色眼","攻守和0")
    b.name("魂","炎").race("水").race()
    print(b)
    print(b.params)
