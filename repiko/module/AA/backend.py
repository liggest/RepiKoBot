
import random
from contextvars import ContextVar
from typing import TypeVar, Generic

import httpx

from AA.file import AAFile

AAFileT = TypeVar("AAFileT", bound=AAFile)

class Backend(Generic[AAFileT]):

    def __init__(self):
        self.files:list[AAFileT] = None
        self._clientVar = ContextVar("client", default=None)

    async def init(self):
        async with httpx.AsyncClient() as client:
            self._clientVar.set(client)
            if not self.files:
                self.files = await self.getFileList()
                print(f"读取到了 {len(self.files)} 个 AA 文件")

    async def getFileList(self) -> list[AAFileT]:
        raise NotImplementedError
    
    async def httpRequest(self, url, param=None, timeout=180):
        client:httpx.AsyncClient = self._clientVar.get()
        if client:
            r = await client.get(url, params=param, timeout=timeout)
            return r.json()

    async def getFileContent(self, file:AAFileT) -> AAFileT:
        raise NotImplementedError

    async def randomFile(self):
        if not self.files:
            await self.init()
            # return None
        # file_count = len(self.files)
        # idx = random.randint(0, file_count-1)
        # file = self.files[idx]
        file = random.choice(self.files)
        if not file.hasContents:
            async with httpx.AsyncClient() as client:
                self._clientVar.set(client)
                file = await self.getFileContent(file)
            if not file:
                return None
            file.save()
        return file
        
    def filterContentsGen(self, file:AAFileT, hasR18=False):
        if "R18" in file.path and not hasR18:
            return
        for c in file.contents:
            cs = c.strip(" \n\r")
            if "R18" in cs:
                if not hasR18:
                    break
                continue
            if cs.startswith("最終更新日"): # 最终更新日 xxx
                continue
            if cs.startswith("【") and cs.endswith("】"): # 【xxx】
                continue
            if "\n" not in cs: # 没有换行
                continue
            yield c

    def chooseContents(self, file:AAFileT, hasR18=False):
        picked = [*self.filterContentsGen(file, hasR18)]
        if picked:
            return random.choice(picked)

    async def randomAA(self, hasR18=False) -> tuple[str, AAFileT]:
        AAtext = None
        file = None
        while not (AAtext):
            file = await self.randomFile()
            if file:
                AAtext = self.chooseContents(file, hasR18)
        return AAtext, file
