from typing import List
from pathlib import Path

saveRoot=Path(".") / "AAFile"
splitter="[SPLIT]\n"

class AAFile(dict):

    @property
    def dir(self) -> str:
        return self["dir"]
    
    @property
    def name(self) -> str:
        return self["filename"]

    @property
    def savePath(self) -> Path:
        return saveRoot / self.dir.lstrip("/") / self.name

    @property
    def hasContents(self):
        return self.get("contents") or self.savePath.exists()

    @property
    def contents(self) -> List[str]:
        content=self.get("contents")
        path=self.savePath
        if not content and path.exists():
            with open(path,"r",encoding="utf-8") as f:
                content=f.read().split(splitter)
        return content

    def save(self):
        content:List[str]=self.get("contents")
        if content:
            path=self.savePath
            if not path.parent.exists():
                path.parent.mkdir(parents=True)
            with open(path,"w",encoding="utf-8") as f:
                f.write(splitter.join(content))

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
