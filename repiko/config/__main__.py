from __future__ import annotations

from repiko.config import Config

if __name__ == "__main__":

    from repiko.core.log import logger
    from typing import TypedDict, TYPE_CHECKING, Literal, Annotated

    if TYPE_CHECKING:
        from repiko.core.bot import Bot

    cfg1=Config("test/test.yaml")
    @cfg1.defaults
    class Test:
        """  Test  """
        a=3
        b=5
        c:int
        d:str
        e:Test

        @property
        def f(self):
            return self._f

        @f.setter
        def f(self,val):
            self._f=val
            self._f=val

        def __init__(self,c=7,f=15,*args,**kw):
            # logger.debug("__init__")
            self.c=c
            self._f=f
            super().__init__()

        # def __setattr__(self:dict, name:str, value:Any):
        #     logger.debug("__setattr__")
        #     super().__setattr__(name,value)
    
    # Test=ConfigMeta.mimic(Test)
    # tst=Test({"c":10},f=20)
    # tst=Test({})
    # logger.debug(tst)
    # logger.debug("a=",tst.a)
    # logger.debug("f=",tst.f)

    cfg2=Config("test/test2.yaml")
    @cfg2.defaults
    class Test2:
        x = 1
        y = ["a", "b", "c"]
        z:str

        class Nested:
            n1:str="name"
            n2:Test2.Nested
        
        n:Nested
    

    # class Test2:

    #     def __init__(self,h):
    #         self.h=h

    #     class Inner:

    #         a=3
    #         b=5
        
    #     inner:Inner

    # Test2=ConfigMeta.mimic(Test2)
    # logger.debug(Test2({"c":10}))

    @cfg2.onInit
    def init(data:Test2,bot:Bot):
        
        import random
        data.h=random.randint(0,10)
        logger.debug(repr(data))

    cfg3=Config("test/test3.json")
    # logger.debug(f"{cfg2.pathKey}  {cfg2.name} {repr(cfg2._loader)}")
    @cfg3.defaults
    class MyConfig:

        a="my_path"
        b="my_token"
        c=[1,2,3]
        d={ "x":3, "y":5 }
        
        text="山重水复疑无路"
        extras:list[str]

    # @cfg2.onUpdate
    # def update(data:MyConfig,bot:Bot):
    #     pass
    
    def test4():
        cfg=Config("test/test4.yml")
        @cfg.defaults
        class Test4:

            inner:Test
            inner2:Test4
            it="good"

            def __repr__(self) -> str:
                return "Test4"

        # logger.debug(f"{cfg.pathKey}  {cfg.name} {repr(cfg._loader)}")

        return cfg.onInit

    cfgOnInit=test4()
    # logger.debug(cfgOnInit)

    botCFG=Config("test/bot_test.toml")
    botCFG2=Config("test/bot_test.yaml")
    botCFG3=Config("test/bot_test.json")
    @botCFG.defaults
    @botCFG2.defaults
    @botCFG3.defaults
    class BotCFG:
        
        class Admin:
            adminQQ = [10086]

        # admin = { "adminQQ":[10086] }
        admin:Admin

        class Bot:
            name = "RepiKo"
            myQQ = 10086

        # bot = { "name":"RepiKo", "myQQ":10086 }
        bot:Bot

        class Connection:
            class WS:
                url:str|None
            class Http:
                url:str|None
                secret:str|None

            http:Http
            ws:WS

        connection:Connection
        # connection = { 
        #     "http":{ "url":None, "secret":None },
        #     "ws":  { "url":None }
        # }

    class InnerTD(TypedDict):
        x:int
        y:int
        z:str

    tdCFG=Config("test/test5.yaml")
    @tdCFG
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

    clsCFG=Config("test/test6.yaml")

    @clsCFG.considerClass
    class InnerCls:
        x:int
        y:int
        z:str
    
    # @clsCFG.defaults
    class CLSCFG:

        a:int
        b:str
        c:set
        d:list
        e:dict
        f:Literal["literal"]
        g:float | str
        inner:InnerCls
        inner2:InnerCls
        nested:CLSCFG

    clsCFG.withDefaults(CLSCFG)


    @cfgOnInit
    @cfg1.onInit
    @cfg2.onInit
    @cfg3.onInit
    @botCFG.onInit
    @tdCFG.onInit
    @clsCFG.onInit
    def init(data:MyConfig,bot:Bot):
        # logger.debug(f"{type(data)}  {repr(data)}")
        return True

    @botCFG.onUpdate
    def update(data:BotCFG,bot:Bot):
        logger.debug(repr(data.admin))
        logger.debug(repr(data.bot))
        logger.debug(repr(data.connection))

    @Config().onInit
    def init(data:dict,bot:Bot):
        for i in range(5):
            data[str(i)]=bot.HEADER
        return True

    @tdCFG.onInit
    # @clsCFG.onInit
    def init(data:TDCFG,bot:Bot):
        # logger.debug(data)
        logger.debug(type(data))
        data["nested"]
        data["nested"]["nested"]
        data["nested"]["nested"]["nested"]

    @clsCFG.onInit
    def init(data:CLSCFG,bot:Bot):
        # logger.debug(data)
        logger.debug(type(data))
        data.nested
        data.nested.nested
        data.nested.nested.nested

    class UnitPattern:
        """  单元  """

        x:str
        y:Annotated[int,"带注释的整数"]
        z:str|None
        w = "啊哇哇哇"

    UnitGroup=Config.Unit("UnitGroup",UnitPattern,"单元组")
    UnitGroup.addDefault("p1",{ "x":"x", "y":3, "z":"z" })
    UnitGroup.addDefault("p2",{ "x":"xx", "y":33, "z":"zz", "w":"ww" })
    UnitGroup.addDefault("p3",UnitPattern({ "x":"xxx", "y":333, "z":"zzz" }))

    unitCFG=Config("test/unit")
    unitCFG.withDefaults(UnitGroup)

    @unitCFG.onInit
    def init(data:dict,bot:Bot):
        # logger.debug(f"{type(data)}  {repr(data)}")
        # logger.debug(data.get("p1"))
        # logger.debug(data.get("p3"))
        # logger.debug(data.get("p5"))
        return True
    
    UnitAllGroup=Config.Unit("UnitAllGroup", dict, "什么都塞的单元组")
    UnitAllGroup.addDefault("admin",anno=BotCFG.Admin)
    UnitAllGroup.addDefault("bot",anno=BotCFG.Bot)
    UnitAllGroup.addDefault("connection",anno=BotCFG.Connection)
    UnitAllGroup.addDefault("unit",anno=UnitPattern)
    UnitAllGroup.addDefault("addition",{ "init":True })

    unitAllCFG=Config("test/unit_all")
    unitAllCFG.withDefaults(UnitAllGroup)

    @unitAllCFG.onInit
    def init(data:dict,bot:Bot):
        logger.debug(f"{type(data)}  {repr(data)}")
        logger.debug(data["admin"])
        logger.debug(data["bot"])
        logger.debug(data["connection"])
        logger.debug(data["unit"])
        return True


    from repiko.core.bot import Bot
    for cfg in Config._configs.values():
        cfg.initUpdate(Bot())
