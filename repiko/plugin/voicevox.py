from typing import Annotated
from itertools import islice
import math

from repiko.core.log import logger
from repiko.core.config import pluginConfig, PluginUnits, Pattern
from repiko.msg.part import Image, Record

from repiko.module.str2image import str2greyPng
from repiko.module.voicevox import VoiceVoxApi, style_map

from LSparser import Command, Events, ParseResult, OPT

(Command("voicevox").names("vv", "vtts")
    .opt(("-list", "-l", "-列表"), OPT.N, "列出可用角色")
    .opt(("-character", "-c", "-角色"), OPT.M, "发音角色")
    .opt(("-style", "-s", "-风格", "-语气"), OPT.M, "发音风格")
    .opt(("-id", "-ID", "-speaker", "-发音人", "-说话人", "-编号"), OPT.M, "发音人编号")
    .opt(("-pitch", "-p", "-音高"), OPT.M, "音高")
    .opt(("-scale", "-intonation", "-is", "-抑扬"), OPT.M, "语音抑扬")
    .opt(("-speed", "-sp", "-语速"), OPT.M, "语音速度")
    .opt(("-log", "-info", "-日志"), OPT.N, "展示更多细节信息")
)

class VioceVoxConfig(Pattern):
    key: Annotated[str | None, "web voicevox api key"]

PluginUnits.addDefault("voicevox", annotation=VioceVoxConfig)

vv: VoiceVoxApi = None

@pluginConfig.on
def initVoiceVox(config:dict, bot):
    global vv
    logger.info("初始化 voicevox ...")
    data: VioceVoxConfig = config.get("voicevox")
    if data and (data.key):
        vv = VoiceVoxApi(data.key)
    else:
        logger.warning("无配置，未初始化 voicevox")

def list_vv_gen():
    style_names = style_map()
    yield "角色列表"
    yield ""
    yield "※指定发音角色和风格："
    yield "【-c 角色名 -s 风格名/左侧ID】或者【-id 右侧中括号内ID】"
    yield ""
    for c in vv.characters.values():
        name_line = f"【{c.display_name}】"
        if c.description:
            name_line = f"{name_line} - {c.description}"
        yield name_line
        if c.name_cn:
            other_names = (c.name, *c.aliases)
        else:
            other_names = c.aliases
        yield "   " + " / ".join(other_names)
        style_gen = (f"{idx}. {style_names.get(s.name, s.name)}[{s.id:02d}]" for idx, s in enumerate(c.styles))
        while line := "    ".join(islice(style_gen, 0, 4)):
            yield "   " + line
        yield ""

async def list_vv():
    logger.info("尝试获取 VoiceVox 角色列表…")
    await vv.get_characters()
    return str2greyPng(list_vv_gen(), "voicevox_characters.png")

def query_info(query: dict[str, str | None], style_names: dict[str, str]):
    q_c_name: str = query['character_name']
    q_s_name: str | None = query['style']
    assert vv.characters
    q_c_display = vv.characters[q_c_name].display_name
    if q_s_name:
        return f"{q_c_display} - {style_names.get(q_s_name, q_s_name)}"
    return q_c_display

def filter_float(value: float | None, min_value: float, max_value: float):
    if value is math.nan or value is None:
        return None
    return max(min(value, max_value), min_value)

@Events.onCmd("voicevox")
async def translate(pr:ParseResult):
    if not vv:
        return ["无可用服务，哑火了…"]
    
    if pr["list"]:
        return [Image(await list_vv()), "详见：https://voicevox.hiroshiba.jp/dormitory/"]

    if not pr.params:
        return ["无字天书不可读呀"]

    text = pr.paramStr
    logs = []

    sid: int | None = pr.getToType("id", None, int)
    if sid is None:
        c_name: str = pr.getByType("character", "俊达萌")
        s_name: str | None = pr.getByType("style")
        query = {"character_name": c_name, "style": s_name}
        speaker = await vv.find_speaker_by_query(query)

        q_info = query_info(query, style_map())

        if speaker is None:
            return [f"未找到 {q_info}"]
        logs.append(f"当前角色风格：{q_info}")
    else:
        speaker = await vv.find_speaker_by_id(sid)
        if speaker is None:
            return [f"未找到 ID 为 {sid} 的发音人"]
    logs.append(f"当前发音人 ID：{speaker.id}")
    
    pitch: float | None = filter_float(pr.getToType("pitch", None, float), *vv.RANGE_PITCH)
    scale: float | None = filter_float(pr.getToType("scale", None, float), *vv.RANGE_INTONATION_SCALE)
    speed: float | None = filter_float(pr.getToType("speed", None, float), *vv.RANGE_SPEED)
    
    logs.append(f"{pitch = !r}  {scale = !r}   {speed = !r}")
    log_info = "\n".join(logs)
    logger.debug(log_info)

    audio = await vv.tts(text, speaker.id, pitch, scale, speed)
    
    if pr["log"]:
        return [log_info, Record(audio, cache=False)]
    
    return [Record(audio, cache=False)]
