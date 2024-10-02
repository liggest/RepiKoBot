from functools import cached_property
from dataclasses import dataclass, field
from pathlib import Path

import tomli

@dataclass
class Style:
    name: str
    id: int
    type: str = "talk"

@dataclass
class Character:
    name: str
    name_cn: str = ""
    aliases: tuple[str] = ()
    description: str = ""
    image: str = ""
    styles: list[Style] = field(default_factory=list, init=False)

    @property
    def display_name(self):
        return self.name_cn or self.name

    @cached_property
    def names(self):
        name_list = [*self.aliases, self.name]
        if self.name_cn:
            name_list.insert(0, self.name_cn)
        return tuple(name.lower() for name in name_list)
            

def load_local(path: Path = Path(__file__).parent / "data" / "characters.toml"):
    with open(path, "rb") as f:
        data:dict[str, dict] = tomli.load(f)
        return { name: Character(**c) for name, c in data.items() }

# {
#     "四国玫碳": "四国めたん",
#     "漆黑的玫碳": "四国めたん",
#     "四国芽丹": "四国めたん",
#     "俊达萌": "ずんだもん",
#     "俊达妖精": "ずんだもん",
#     "毛豆精": "ずんだもん",
#     "豆打兽": "ずんだもん",
#     "春日部䌷": "春日部つむぎ",
#     "雨晴晴雨": "雨晴はう",
#     "雨晴hau": "雨晴はう",
#     "波音律": "波音リツ",
#     # "玄野武宏": "玄野武宏",
#     "玄武": "玄野武宏",
#     # "白上虎太郎": "白上虎太郎",
#     "白虎": "白上虎太郎",
#     "青山龙星": "青山龍星",
#     "青龙": "青山龍星",
#     "冥鸣himari": "冥鳴ひまり",
#     "九州宇宙": "九州そら",
#     "模型娘饼子": "もち子さん",
#     "剑崎雌雄": "剣崎雌雄",
#     "whitecul": "WhiteCUL",
#     "后鬼": "後鬼",
#     # "No.7": "No.7",
#     # "ちび式じい": "ちび式じい"
#     "樱歌miko": "櫻歌ミコ",
#     "小夜/sayo": "小夜/SAYO",
#     "nurserobot typet": "ナースロボ＿タイプＴ",
#     "小护士": "ナースロボ＿タイプＴ",
#     "圣骑士 红缨": "†聖騎士 紅桜†",
#     # "雀松朱司": "雀松朱司"
#     "朱雀": "雀松朱司",
#     "麒岛宗麟": "麒ヶ島宗麟",
#     "麒麟": "麒ヶ島宗麟",
#     "春歌nana": "春歌ナナ",
#     "猫使R": "猫使アル",
#     "猫使B": "猫使ビィ",
#     "中国兔": "中国うさぎ",
#     "栗田栗子": "栗田まろん",
#     "IL碳": "あいえるたん",
#     "满别花丸": "満別花丸",
#     "琴咏nia": "琴詠ニア",
#     # "幽灵酱": "ユーレイちゃん",
#     # "九十九酱": "ツクモちゃん",
#     # "中部剑": "中部つるぎ",
#     # "晓记mitama": "暁記ミタマ",
#     # "里石yuka": "里石ユカ",
#     # "瑞泽takuto": "瑞澤タクト",
# }

def style_map():
    return {
        "ノーマル": "普通",
        "あまあま": "甜甜",
        "ツンツン": "刺刺",
        "セクシー": "Sexy",
        "ささやき": "悄悄",
        "ヒソヒソ": "低声",
        "ヘロヘロ": "弱弱",
        "なみだめ": "哭哭",
        "クイーン": "女王",
        "喜び": "喜悦",
        "ツンギレ": "窝火",
        "悲しみ": "悲伤", 
        "ふつう": "普通",
        "わーい": "兴奋",
        "びくびく": "害怕",
        "おこ": "生气",
        "びえーん": "哭哭",
        "熱血": "热血",
        "不機嫌": "不快",
        "しっとり": "舒缓",
        "かなしみ": "悲伤",
        "囁き": "悄悄",
        "セクシー／あん子": "Sexy/An子",
        "泣き": "难受",
        "怒り": "怒怒",
        "のんびり": "悠闲",
        "たのしい": "开心",
        "かなしい": "悲伤",
        "人間ver.": "人类",
        "ぬいぐるみver.": "玩偶",
        "人間（怒り）ver.": "人类（怒）",
        "鬼ver.": "鬼",
        "アナウンス": "通知",
        "読み聞かせ": "讲故事",
        "第二形態": "第二形态",
        "ロリ": "萝莉",
        "楽々": "轻松",
        "恐怖": "恐怖",
        "内緒話": "悄悄话",
        "おちつき": "平静",
        "うきうき": "雀跃",
        "人見知り": "害羞",
        "おどろき": "惊讶",
        "こわがり": "害怕",
        "へろへろ": "弱弱",
        "元気": "元气",
        "ぶりっ子": "装可爱",
        "ボーイ": "Boy",
    }
