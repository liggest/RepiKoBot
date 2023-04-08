
# from repiko.msg.core import MCore
# from repiko.core.constant import EventNames
from repiko.core.config import pluginConfig, PluginUnits, Pattern
# from repiko.module.google_translation import gTranslator
from repiko.module.deepl_translation import DeepTrans,Formality

from typing import Annotated

from LSparser import *

# (Command("translate").names("ts").opt("-from",OPT.M,"源语言").opt("-to",OPT.M,"目标语言").opt("-p",OPT.N,"显示发音")
#     .opt("-d",OPT.N,"检测语言").opt("-donly",OPT.N,"只检测语言")
#     .opt("-en",OPT.N,"翻译到英语").opt("-ja",OPT.N,"翻译到日语").opt("-ru",OPT.N,"翻译到俄语").opt("-de",OPT.N,"翻译到德语")
#     .opt("-es",OPT.N,"翻译到西语")
# )

(Command("translate").names("tl").opt(("-from","-从"),OPT.M,"源语言").opt(("-to","-到"),OPT.M,"目标语言") 
    # .opt("-p",OPT.N,"显示发音")
    # .opt("-d",OPT.N,"检测语言").opt("-donly",OPT.N,"只检测语言")
    .opt(("-zh","-ZH","-中文","-汉语","-中"),OPT.N,"翻译到中文")
    .opt(("-en","-EN","-英语","-英"),OPT.N,"翻译到英语").opt(("-ja","-JA","-日语","-日"),OPT.N,"翻译到日语")
    .opt(("-ru","-RU","-俄语","-俄"),OPT.N,"翻译到俄语").opt(("-de","-DE","-德语","-德"),OPT.N,"翻译到德语")
    .opt(("-es","-ES","-西班牙语","-西语","-西"),OPT.N,"翻译到西班牙语")
    .opt(("-pt","-PT","-葡萄牙语","-葡语","-葡"),OPT.N,"翻译到葡萄牙语")
    .opt(("-eng","-Eng"),OPT.N,"翻译到英式英语").opt(("-us","-US"),OPT.N,"翻译到美式英语")
    .opt(("-mf","-MF","-正经"),OPT.N,"翻译结果可能更正经").opt(("-lf","-LF","-不正经"),OPT.N,"翻译结果可能更不正经")
)

t:DeepTrans=None

# cfg=Config("trans.toml")

class TransConfig(Pattern):
    key:Annotated[str | None,"DeepL api key"]

PluginUnits.addDefault("trans",annotation=TransConfig)

# @cfg.withDefaults({ "key":"" }).onInit
@pluginConfig.on
def initTrans(config:dict, bot):
    global t
    data:TransConfig=config.get("trans")
    if data and (data.key):
        t=DeepTrans()
        t.init(data.key)

@Events.onCmd("translate")
def translate(pr:ParseResult):
    if not t:
        return ["坏了啦，翻译什么的做不到了啦…"]
    if len(pr.params)==0:
        return ["给点东西让我翻译嘛"]
    text=pr.paramStr
    fromLan=pr.getByType("from")
    toLan="中文"
    for lang in ("en","ja","ru","de","es","pt"):
        if pr.getByType(lang,False,bool):
            toLan=lang
            break
    if pr["eng"]:
        toLan="英式英语"
    elif pr["us"]:
        toLan="美式英语"
    toLan=pr.getByType("to",toLan)
    formality=Formality.DEFAULT
    if pr["mf"]:
        formality=Formality.PREFER_MORE
    elif pr["lf"]:
        formality=Formality.PREFER_LESS
    return t.translate(text,fromLan=fromLan,toLan=toLan,formality=formality)

# @Events.on(EventNames.MsgCoreInit)
# def coreInit(core:MCore):
#     initTrans(core)

# @Events.onCmd("translate")
# def translate(pr:ParseResult):
#     if len(pr.params)==0:
#         return ["给点东西让我翻译嘛"]
#     text=pr.paramStr
#     a=gTranslator()
#     donly=pr.getByType("donly",False,bool)
#     if donly:
#         return a.detectonly(text)
#     fromlan=pr.getByType("from","auto")
#     tolan="cn"
#     for lang in ("en","ja","ru","de","es"):
#         if pr.getByType(lang,False,bool):
#             tolan=lang
#             break
#     tolan=pr.getByType("to",tolan)
#     poun=pr.getByType("p",False,bool)
#     dtct=pr.getByType("d",False,bool)
#     return a.trans(text,fromlan=fromlan,tolan=tolan,poun=poun,showDetect=dtct)
# @Events.onCmd("translate")
# def translate(_):
#     return ["呜呜呜谷歌翻译寄了啊啊啊啊啊"]
