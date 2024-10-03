
from repiko.core.log import logger
from repiko.module.nlp.to_kana.pinyin import Pinyin2Kana

from LSparser import Command, Events, ParseResult, OPT

(Command("tokana").names("假名", "假名化", "太君说", "大佐说")
 .opt(["-style", "-s", "-风格"], OPT.M, "转换风格")
 .opt(["-s1"], OPT.N, "转换风格 1")
 .opt(["-s2"], OPT.N, "转换风格 2")
 .opt(["-s3"], OPT.N, "转换风格 3")
)

converter: Pinyin2Kana | None = None

@Events.onCmd("tokana")
def to_kana(pr:ParseResult):
    global converter

    v: str = pr.getToType("style", "1", str)
    for i in range(0, 4):
        if pr[f"s{i}"]:
            v = str(i)
            break
    v = f"s{v}"
    if not converter or converter._style.name != v:
        converter = Pinyin2Kana(v)
        logger.info(f"初始化拼音-假名转换器，风格 {converter._style.name}")

    text = pr.paramStr
    print(converter._map["shi"])
    return ["".join(converter.convert(text))]
