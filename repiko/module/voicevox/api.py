from typing import TypedDict

import httpx

from voicevox.character import load_local, Character, Style, style_map

class Features(TypedDict):
    permitted_synthesis_morphing: str

class StyleDict(TypedDict):
    name: str
    id: int
    type: str

class Speaker(TypedDict):
    supported_features: Features
    name: str
    speaker_uuid: str
    styles: list[StyleDict]
    version: str

class SpeakerQuery(TypedDict):
    character_name: str
    style: int | str | None

class ApiLimit(TypedDict):
    points: int
    resetInHours: float

class VoiceVoxApi:

    # VOICEVOX = "https://voicevox.hiroshiba.jp"
    # API_BASE = "https://api.su-shiki.com/v2/voicevox/audio/"
    API_BASE = "https://deprecatedapis.tts.quest/v2/voicevox/"
    API_TTS = f"{API_BASE}audio/"
    API_SPEAKERS = f"{API_BASE}speakers/"

    characters: dict[str, Character] | None = None
    id2styles: dict[int, Style] | None = None

    def __init__(self, key: str):
        self.key = key

    async def get_speakers(self) -> list[Speaker]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(self.API_SPEAKERS, params={"key": self.key})
            return response.json()

    async def get_characters(self):
        if self.characters is not None:
            return self.characters
        self.__class__.characters = load_local()
        self.__class__.id2styles = {}
        characters = self.__class__.characters
        id2styles = self.__class__.id2styles  # 也建立 id 到 style 的映射
        speakers = await self.get_speakers()  # 从 json 数据补充 style
        for speaker in speakers:
            name = speaker["name"]
            if not (c := characters.get(name)):
                characters[name] = Character(name)
            for style in speaker["styles"]:
                s = Style(**style)
                c.styles.append(s)
                id2styles[s.id] = s
                
        return characters

    async def find_character(self, name: str):
        characters = await self.get_characters()
        if c := characters.get(name):
            return c
        name = name.lower()
        for c in characters.values():
            if any(name in n for n in c.names):
                return c

    def find_style(self, name: int | str | None, character: Character):
        style_id: int | None = None
        if not name:
            style_id = 0
        elif isinstance(name, int):
            style_id = name
        elif name.isdigit():
            style_id = int(name)
        if style_id is not None:
            if 0 <= style_id <= len(character.styles):
                return character.styles[style_id]
        name = str(name).lower()
        style_names = style_map()
        if any(s := style for style in character.styles if 
               name in style_names.get(style.name, "").lower() or
               name in style.name.lower()  # 在 style_map 对应的名字里，或在原名里
            ):
            return s

    async def find_speaker_by_id(self, sid: int):
        await self.get_characters()
        return self.id2styles.get(sid)
    
    async def find_speaker_by_query(self, query: SpeakerQuery):
        c = await self.find_character(query["character_name"])
        if c:
            query["character_name"] = c.name
            if s := self.find_style(query["style"], c):
                query["style"] = s.name
                return s

    # async def find_speaker_id(self, speaker: str | int, style: int | str | None = None):
    #     # speaker name or speaker id
    #     if isinstance(speaker, int):
    #         if speaker in self.id2styles:
    #             return speaker
    #         else:
    #             return None
    #     c = await self.find_character(speaker)
    #     if c:
    #         if s := self.find_style(style, c):
    #             return s.id

    RANGE_SPEED = (0.5, 2.0)
    RANGE_PITCH = (-0.15, 0.15)
    RANGE_INTONATION_SCALE = (0.0, 2.0)

    async def tts(self, text: str, speaker: int,
                  pitch: float | None = None, 
                  intonation_scale: float | None = None,
                  speed: float | None = None) -> bytes:
        params = {"speaker": speaker}
        if pitch is not None:
            params["pitch"] = pitch
        if intonation_scale is not None:
            params["intonation_scale"] = intonation_scale
        if speed is not None:
            params["speed"] = speed
        async with httpx.AsyncClient(timeout=httpx.Timeout(20, read=60)) as client:
            response = await client.post(
                self.API_TTS,
                data={"text": text, "key": self.key},
                params=params,
            )
            response.raise_for_status()
            return response.content
        
    async def check_limit(self) -> ApiLimit:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get("https://deprecatedapis.tts.quest/v2/api/", params={"key": self.key})
            return response.json()

