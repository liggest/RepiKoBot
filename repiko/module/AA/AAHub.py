from typing import Generator, Any
import html

from AA.backend import Backend
from AA.file import AAFile

class AAHubFile(AAFile):

    @property
    def dir(self) -> str:  
        if self.kind:  # 手动填充
            return self.get("dir", "")
        return self.path.removesuffix(f"/{self.name}.mlt")

    @property
    def path(self) -> str:
        if self.kind:
            return f"{self.dir}/{self.name}.mlt"
        return f"{self['path']}.mlt"
    
    @property
    def url(self) -> str:
        if self.kind:
            return f"{self['path']}.json"
        return ""

    @property
    def name(self) -> str:
        return self["name"]

    @property
    def updateInfo(self) -> str:
        return self.get("updated", "")

    @property
    def kind(self) -> int:
        return self.get("kind", 0)  # 0 即 kind 不存在
    
    @property
    def _getSelfContents(self) -> list[str] | None:
        contents:list[dict[str, str]] = self.get("aa")
        return contents and [aa["value"] for aa in contents]

class AAHub(Backend[AAHubFile]):
    
    baseUrl = r"https://aa-storage.aahub.org/"
    folderUrl = f"{baseUrl}folders.json"
    contentBaseUrl = f"{baseUrl}folders/"

    @classmethod
    def getFileListGen(cls, fileList:list[dict[str, str]], dir = "") -> Generator[AAHubFile, Any, Any]:
        if not fileList:
            return
        for file in fileList:
            if file.get("kind", 0) == 2:
                file["dir"] = dir
                yield AAHubFile(file)
            elif child := file.get("folders"):
                yield from cls.getFileListGen(child, file["path"])

    async def getFileList(self) -> list[AAHubFile]:
        rj:dict = await self.httpRequest(self.folderUrl)
        if rj and (folders := rj.get("folders")):
            return [*self.getFileListGen(folders)]
        return []
    
    async def getFileContent(self, file:AAHubFile):
        url = file.url
        if url:
            rj:dict = await self.httpRequest(f"{self.contentBaseUrl}{file.url}")
            if not rj:
                return None
            if contents := rj.get("aa"):
                contents:list[dict[str, str]]
                for aa in contents:
                    aa["value"] = html.unescape(aa["value"]).replace("\r\n","\n")
            return AAHubFile(rj)
