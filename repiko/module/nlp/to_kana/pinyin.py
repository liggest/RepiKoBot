
from enum import Enum
from pathlib import Path

from pypinyin import lazy_pinyin

class KanaStyle(Enum):
    s1 = "pinyin-kana.tsv"
    s2 = "jpinyin.tsv"
    s3 = "pinyin_to_kana.tsv"

_here = Path(__file__).parent

def load_map(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        lines = (line.strip().split() for line in f)
        return {k: v for k, v in lines}

class Pinyin2Kana:

    _map: dict[str, str] = {}
    _style: KanaStyle = KanaStyle.s1

    def __init__(self, style: str | KanaStyle = _style) -> None:
        if isinstance(style, str):
            style: KanaStyle = KanaStyle._member_map_.get(style, self._style)
        self._style = style
        self._map = load_map(_here / "data" / self._style.value)

    def convert(self, text: str | list[str]):
        return [ self._map.get(item, item) for item in lazy_pinyin(text, v_to_u=True) ]
