
from typing import Generator, Any
import html

from AA.backend import Backend
from AA.file import AAFile

class AAMZFile(AAFile):

    @property
    def dir(self) -> str:
        return self["dir"]
    
    @property
    def name(self) -> str:
        return self["filename"]

    @property
    def path(self) -> str:
        return f"{self.dir.lstrip('/')}/{self.name}"

    @property
    def _selfContents(self) -> list[str] | None:
        return self.get("contents")

    @property
    def hash(self) -> str:
        return self["hash"]

    @property
    def size(self):
        return self["filesize"]

    @property
    def isNew(self):
        return self["isNew"]

    @property
    def isUp(self):
        return self["isUp"]

    @property
    def isF(self):
        return self["isF"]

class AAMZ(Backend[AAMZFile]):
    
    baseUrl = r"https://aa.yaruyomi.com/"
    metaUrl = r"api/events/url"

    def __init__(self):
        super().__init__()
        self.listUrl = ""
        self.contentUrl = ""

    async def getUrls(self):
        rj = await self.httpRequest(f"{self.baseUrl}{self.metaUrl}")
        if rj:
            self.listUrl = rj["events"]["matomeFileList"]
            self.contentUrl = rj["events"]["matomeFileContents"]
            return True

    @classmethod
    def getFileListGen(cls, fileList:list[dict[str, str]]) -> Generator[AAMZFile, Any, Any]:
        if not fileList:
            return
        for file in fileList:
            if file.get("filename", "").endswith(".mlt"):
                yield AAMZFile(file)
            elif child := file.get("child"):
                yield from cls.getFileListGen(child)

    async def getFileList(self) -> list[AAMZFile]:
        if self.listUrl or await self.getUrls():
            rj = await self.httpRequest(self.listUrl)
            if rj:
                return [*self.getFileListGen(rj)]
        return []
    
    async def getFileContent(self, file:AAMZFile):
        if self.contentUrl or await self.getUrls():
            rj:dict = await self.httpRequest(self.contentUrl, param={"hash":file.hash})
            if not rj:
                return None
            if contents := rj.get("contents"):
                contents: list[str]
                rj["contents"] = [ html.unescape(c).replace("\r\n","\n") for c in contents ]
            return AAMZFile(rj)
