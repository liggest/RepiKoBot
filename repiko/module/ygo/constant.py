from enum import Enum,IntFlag

class CardType(IntFlag):
    Monster=0x1
    Spell=0x2
    Trap=0x4
    #N/A=0x8
    Normal=0x10 #通常（怪兽）
    Effect=0x20
    Fusion=0x40
    Ritual=0x80
    TrapMonster=0x100
    Spirit=0x200
    Union=0x400
    Gemini=0x800
    Tuner=0x1000
    Synchro=0x2000
    Token=0x4000
    #N/A=0x8000
    Quick_Play=0x10000
    Continuous=0x20000
    Equip=0x40000
    Field=0x80000
    Counter=0x100000
    Flip=0x200000
    Toon=0x400000
    Xyz=0x800000
    Pendulum=0x1000000
    SPSummon=0x2000000
    Link=0x4000000

    def __str__(self):
        if self in cardType2str:
            return cardType2str[self]
        return super().__str__()
    
    __repr__=__str__

    @staticmethod
    def fromStr(text):
        return str2cardType.get(text)
        

cardType2str={
    CardType.Monster:"怪兽",
    CardType.Normal:"通常",
    CardType.Effect:"效果",
    CardType.Tuner:"调整",
    CardType.Gemini:"二重",
    CardType.Flip:"反转",
    CardType.Union:"同盟",
    CardType.Spirit:"灵魂",
    CardType.Toon:"卡通",
    CardType.Fusion:"融合",
    CardType.Synchro:"同调",
    CardType.Xyz:"超量",
    CardType.Pendulum:"灵摆",
    CardType.Ritual:"仪式",
    CardType.Link:"连接",
    CardType.TrapMonster:"陷阱怪兽",
    CardType.SPSummon:"特殊召唤",
    CardType.Token:"衍生物",
    CardType.Spell:"魔法",
    CardType.Trap:"陷阱",
    CardType.Quick_Play:"速攻",
    CardType.Continuous:"永续",
    CardType.Equip:"装备",
    CardType.Field:"场地",
    CardType.Counter:"反击"
}

str2cardType=dict( map( reversed,cardType2str.items() ) )
str2cardType["XYZ"]=CardType.Xyz

class CardAttribute(IntFlag):
    Earth=0x01
    Water=0x02
    Fire=0x04
    Wind=0x08
    Light=0x10
    Dark=0x20
    Divine=0x40 #神属性

    def __str__(self):
        if self in cardAttribute2str:
            return cardAttribute2str[self]
        return super().__str__()
    
    __repr__=__str__

    @staticmethod
    def fromStr(text):
        return str2cardAttribute[text]

cardAttribute2str={
    CardAttribute.Earth:"地",
    CardAttribute.Water:"水",
    CardAttribute.Fire:"炎",
    CardAttribute.Wind:"风",
    CardAttribute.Light:"光",
    CardAttribute.Dark:"暗",
    CardAttribute.Divine:"神"
}

str2cardAttribute=dict( map( reversed,cardAttribute2str.items() ) )

class CardRace(IntFlag):
    Warrior=0x1
    Spellcaster=0x2
    Fairy=0x4
    Fiend=0x8
    Zombie=0x10
    Machine=0x20
    Aqua=0x40
    Pyro=0x80
    Rock=0x100
    WingedBeast=0x200
    Plant=0x400
    Insect=0x800
    Thunder=0x1000
    Dragon=0x2000
    Beast=0x4000
    Beast_Warrior=0x8000
    Dinosaur=0x10000
    Fish=0x20000
    SeaSerpent=0x40000
    Reptile=0x80000
    Psychic=0x100000
    Divine_Beast=0x200000
    CreatorGod=0x400000
    Wyrm=0x800000
    Cyberse=0x1000000
    Illusion=0x2000000

    def __str__(self):
        if self in cardRace2str:
            return cardRace2str[self]
        return super().__str__()
    
    __repr__=__str__

    @staticmethod
    def fromStr(text):
        return str2cardRace[text]

cardRace2str={
    CardRace.Warrior:"战士",
    CardRace.Spellcaster:"魔法师",
    CardRace.Fairy:"天使",
    CardRace.Fiend:"恶魔",
    CardRace.Zombie:"不死",
    CardRace.Machine:"机械",
    CardRace.Aqua:"水",
    CardRace.Pyro:"炎",
    CardRace.Rock:"岩石",
    CardRace.WingedBeast:"鸟兽",
    CardRace.Plant:"植物",
    CardRace.Insect:"昆虫",
    CardRace.Thunder:"雷",
    CardRace.Dragon:"龙",
    CardRace.Beast:"兽",
    CardRace.Beast_Warrior:"兽战士",
    CardRace.Dinosaur:"恐龙",
    CardRace.Fish:"鱼",
    CardRace.SeaSerpent:"海龙",
    CardRace.Reptile:"爬虫类",
    CardRace.Psychic:"念动力",
    CardRace.Divine_Beast:"幻神兽",
    CardRace.CreatorGod:"创造神",
    CardRace.Wyrm:"幻龙",
    CardRace.Cyberse:"电子界",
    CardRace.Illusion:"幻想魔"
}

str2cardRace=dict( map( reversed,cardRace2str.items() ) )
str2cardRace["爬虫"]=CardRace.Reptile

class LinkMark(IntFlag):
    BottomLeft=0x001
    Bottom=0x002
    BottomRight=0x004
    Left=0x008
    #Middle=0x010
    Right=0x020
    TopLeft=0x040
    Top=0x080
    TopRight=0x100

    def toNumber(self): # 1-9
        binstr=bin(self.value)[2:]
        return len(binstr)

    def __str__(self):
        return linkMark2str[ self.toNumber()-1 ]

    # __repr__=__str__

    @staticmethod
    def fromNumber(num,withmid=False):
        if withmid:
            if num>4:
                num=num-1
        # return number2linkMark[num-1]
        return list(LinkMark)[num-1]

# number2linkMark=[lm for lm in LinkMark]
# linkMark2str=[" ◣"," ↓ ","◢ ","←","   ","→"," ◤"," ↑ ","◥ "]
linkMark2str=["↙","⬇","↘","⬅","    ","➡","↖","⬆","↗"] # "⏺"


class CardCategory(Enum):
    魔陷破坏=0x01        #SpellTrapDestroy=0x01
    怪兽破坏=0x02        #MonsterDestroy=0x02
    除外=0x04            #Remove=0x04
    送去墓地=0x08         #ToGrave=0x08
    返回手卡=0x10          #ToHand=0x10
    返回卡组=0x20           #ToDeck=0x20
    手卡破坏=0x40            #DiscardHand=0x40
    卡组破坏=0x80             #DiscardDeck=0x80
    抽卡辅助=0x100             #Draw=0x100
    卡组检索=0x200              #Search=0x200
    卡片回收=0x400               #Recycle=0x400
    表示形式=0x800                #Position=0x800
    控制权=0x1000                  #Control=0x1000
    攻守变化=0x2000                 #AtkDefChange=0x2000
    贯通伤害=0x4000                  #Brionac=0x4000 #穿刺/贯通
    多次攻击=0x8000                   #MultiAttack=0x8000
    攻击限制=0x10000                   #AttackRestrain=0x10000 #攻击限制
    直接攻击=0x20000
    特殊召唤=0x40000
    衍生物=0x80000
    种族相关=0x100000
    属性相关=0x200000
    效果伤害=0x400000
    回复=0x800000
    破坏耐性=0x1000000
    效果耐性=0x2000000
    指示物=0x4000000
    赌博=0x8000000
    融合相关=0x10000000
    同调相关=0x20000000
    超量相关=0x40000000
    效果无效=0x80000000

    def __str__(self):
        return self.name

    __repr__=__str__
