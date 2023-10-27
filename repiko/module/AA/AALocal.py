
from pathlib import Path
import html
import random

from AA.backend import Backend
from AA.file import AAFile, saveRoot, splitter

class LocalFile(AAFile):
    
    def __init__(self, path: Path):
        super().__init__()
        self.savePath = path

    @property
    def name(self) -> str:
        path:Path = self["path"]
        return path.name
    
    @property
    def path(self) -> str:
        path:Path = self["path"]
        return path.as_posix()

    @property
    def savePath(self) -> Path:
        return self["path"]

    @savePath.setter
    def savePath(self, val:Path):
        self["path"] = val

    @property
    def _selfContents(self) -> list[str] | None:
        return self.get("contents")

    @_selfContents.setter
    def _selfContents(self, val:list[str]):
        if val:
            self["contents"] = val

    @property
    def contents(self):
        content = self._selfContents
        if not content:
            try:
                with self.savePath.open(encoding="cp932") as f:  # shiftJIS
                    content = f.read().split(splitter)
            except UnicodeDecodeError:
                with self.savePath.open(encoding="utf-8") as f:  # utf-8
                    content = f.read().split(splitter)
        return content
    
    def save(self):
        return  # 都在本地了，不保存

class Local(Backend[LocalFile]):

    root = saveRoot

    def __init__(self, root:Path=None):
        self.files:list[LocalFile] = None
        if root:
            root = Path(root)
            if root.is_dir():
                self.root = root
            else:
                print(f"未找到提供给本地 AA 库的路径 {root.as_posix()}")
        else:
            print("未提供路径给本地 AA 库")
        print(f"将使用 {self.root.as_posix()} 作为 AA 库根目录")

    async def init(self):
        self.syncInit()
            
    def syncInit(self):
        if not self.files:
            self.files = self.syncGetFileList()
            print(f"读取到了 {len(self.files)} 个 AA 文件")
        
    async def getFileList(self):
        return self.syncGetFileList()
    
    def syncGetFileList(self):
        return [LocalFile(path) for path in self.root.glob("**/*.mlt")]
    
    async def getFileContent(self, file:LocalFile):
        return self.syncGetFileContent(file)

    def syncGetFileContent(self, file:LocalFile):
        if file.savePath.is_file():
            contentFile = LocalFile(file.savePath)
            contentFile._selfContents = [ html.unescape(c).replace("\r\n","\n") for c in file.contents ]
            return contentFile

    async def randomFile(self):
        return self.syncRandomFile()

    def syncRandomFile(self):
        if not self.files:
            self.syncInit()
        file = random.choice(self.files)
        if not file.hasContents:
            file = self.syncGetFileContent(file)
            if not file:
                return None
            # file.save()
        return file

    async def randomAA(self, hasR18=False):
        return self.syncRandomAA(hasR18)

    def syncRandomAA(self, hasR18=False) -> tuple[str, LocalFile]:
        AAtext = None
        file = None
        while not (AAtext):
            file = self.syncRandomFile()
            if file:
                AAtext = self.chooseContents(file, hasR18)
        return AAtext, file

