from pathlib import Path

saveRoot = Path(".") / "AAFile"
splitter = "[SPLIT]\n"

class AAFile(dict):
    
    @property
    def name(self) -> str:
        raise NotImplementedError
    
    @property
    def path(self) -> str:
        raise NotImplementedError

    @property
    def savePath(self):
        return saveRoot / self.path
    
    @property
    def _getSelfContents(self) -> list[str] | None:  # get contents in self
        raise NotImplementedError

    @property
    def hasContents(self):
        return bool(self._getSelfContents) or self.savePath.exists()
    
    @property
    def contents(self):
        content = self._getSelfContents
        path = self.savePath
        if not content and path.exists():
            with path.open(encoding="utf-8") as f:
                content = f.read().split(splitter)
        return content
    
    def save(self):
        content = self._getSelfContents
        if content:
            path = self.savePath
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                f.write(splitter.join(content))
