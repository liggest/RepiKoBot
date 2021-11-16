
from .constant import *

class Card():
    def __init__(self,types=tuple() ):
        self.id=None #卡号
        self.name=None #卡名（中文）
        self.jpname=None #卡名（日文）
        self.enname=None #卡名（英文）
        self.effect=None #效果文本

        self.ot=None #ot状态
        self.set=set() #系列
        self.cardType=set() #卡片类型
        self.limit=None #禁限

        self.category=set() #效果种类
        
        self.isRD=False

        # 一系列链接
        self.img=None
        self.database=None
        self.QA=None
        self.wiki=None
        self.yugipedia=None
        self.ygorg=None
        self.ourocg=None
        self.script=None
        self.ocgRule=None

        self.fillCardType(*types)

        if self.isMonster:
            self.attack=None #攻击力
            self.defence=None #守备力
            self.level=None #等级
            self.race=None #种族
            self.attribute=None #属性
            if self.isXyz:
                self.rank=None
            if self.isP:
                self.Pmark=[None,None]
            if self.isLink:
                self.linknum=None
                self.linkmark=set()

    def __str__(self):
        return self.info()
    
    __repr__=__str__
    
    @property
    def isMonster(self):
        return CardType.Monster in self.cardType
    
    @property
    def isXyz(self):
        return CardType.Xyz in self.cardType

    @property
    def isP(self):
        return CardType.Pendulum in self.cardType

    @property
    def isLink(self):
        return CardType.Link in self.cardType

    def fillCardType(self,*types):
        for t in types:
            if isinstance(t,str):
                ct=CardType.fromStr(t)
                if ct:
                    self.cardType.add(ct)
                else:
                    self.cardType.add(t)
            else:
                self.cardType.add(t)
    
    def checkAndFill(self,text,filltext,default=""):
        if not text is None:
            return filltext.format( text )
        return default

    def info(self):
        result=""
        result+=self.checkAndFill(self.name,"卡名 {}\n")
        result+=self.checkAndFill(self.jpname,"日文名 {}\n")
        result+=self.checkAndFill(self.enname,"英文名 {}\n")
        if len(self.cardType)>0: #卡片种类
            typelist=[ str(ct) for ct in self.cardType ]
            result+=" ".join(typelist)+"\n"
        if self.isRD:
            result+="RUSH DUEL  "
        else:
            result+=self.checkAndFill(self.id,"密码 {}")+"  "
        result+=self.checkAndFill(self.limit,"{}") #禁限
        result+=self.checkAndFill(self.ot,"  {}\n","\n") #O/T
        if len(self.set)>0: #卡片种类
            result+="系列 "+" ".join(self.set)+"\n"
        if self.isMonster:
            result+=self.checkAndFill(self.race,"{}族")
            result+=self.checkAndFill(self.attribute,"  {}属性")
            if self.isXyz:
                result+=self.checkAndFill(self.rank,"  {}阶\n")
            if self.isLink:
                result+=self.checkAndFill(self.linknum,"  LINK{}\n")
                result+=self.checkAndFill(self.attack,"攻击力 {}\n")
                # marklist=["   "]*8
                middle=linkMark2str[len(linkMark2str)//2]
                marklist=[middle]*8
                for i,lm in enumerate(LinkMark):
                    if lm in self.linkmark:
                        marklist[i]=str(lm)
                marktext="{0[5]}{0[6]}{0[7]}\n{0[3]}{1}{0[4]}\n{0[0]}{0[1]}{0[2]}".format(marklist,middle)
                for line in marktext.split("\n"):
                    if line.strip():
                        result+=line+"\n"
            else:
                if not self.isXyz:
                    result+=self.checkAndFill(self.level,"  {}星\n")
                result+=self.checkAndFill(self.attack,"攻击力 {}")
                result+=self.checkAndFill(self.defence,"  守备力 {}\n")
            if self.isP:
                if self.effect and not self.effect.startswith("←"):
                    ptext=f"←{self.Pmark[0]} 【灵摆】 {self.Pmark[1]}→\n"
                    result+=ptext
        effecttext=self.checkAndFill(self.effect,"{}")
        result+=effecttext.replace("・","·")
        return result

    def fromCDBTuple(self,t,setdict=None,lfdict=None):
        self.name=t[0]
        self.effect=t[1]
        self.id=t[2]
        if t[3]==1:
            self.ot="OCG专有卡"
        elif t[3]==2:
            self.ot="TCG专有卡"
        if t[4]!=0:
            self.id=t[4]
        if setdict:
            setval=t[5]
            while setval!=0:
                setname=setdict.get( setval & 0xFFFF ,None)
                if setname:
                    self.set.add(setname)
                setval=setval>>16
        if lfdict:
            lfname=["禁止","限制","准限制","无限制"]
            lfnum=lfdict.get(self.id,3)
            self.limit=lfname[lfnum]
        self.cardType=Card.bit2CardTypes(t[6])
        if self.isMonster:
            self.attack=Card.dealAtkDef(t[7])
            self.level=Card.dealLevel(t[9])
            if self.isLink:
                self.linkmark=Card.bit2Linkmark(t[8])
                self.linknum=self.level
            else:
                self.defence=Card.dealAtkDef(t[8])
            if self.isXyz:
                self.rank=self.level
            if self.isP:
                self.Pmark=Card.getPmark(t[9])
            self.race=Card.bit2Race(t[10])
            self.attribute=Card.bit2Attribute(t[11])
            self.category=Card.bit2Category(t[12])

    @staticmethod
    def dealAtkDef(val):
        if val<0:
            return "?"
        return val

    @staticmethod
    def dealLevel(val):
        return val & 0b1111

    @staticmethod
    def getPmark(val):
        pl=(val & 0xF000000)>>24
        pr=(val & 0x00F0000)>>16
        return [pl,pr]

    @staticmethod
    def bit2Set(bit,enum):
        s=set()
        for x in enum:
            if x.value & bit!=0:
                s.add(x)
        return s    

    @staticmethod
    def bit2Item(bit,enum):
        for x in enum:
            if x.value & bit!=0:
                return x
        return None    
        
    @staticmethod
    def funcWithEnum(func,enum):
        def wrapper(bit):
            return func(bit,enum)
        return wrapper    

    bit2CardTypes=funcWithEnum.__func__(bit2Set.__func__,CardType)
    bit2Race=funcWithEnum.__func__(bit2Item.__func__,CardRace)
    bit2Attribute=funcWithEnum.__func__(bit2Item.__func__,CardAttribute)
    bit2Linkmark=funcWithEnum.__func__(bit2Set.__func__,LinkMark)
    bit2Category=funcWithEnum.__func__(bit2Set.__func__,CardCategory)

#Card.bit2CardTypes=Card.funcWithEnum(Card.bit2Set,CardType)

if __name__ == "__main__":
    print(CardType.Token)