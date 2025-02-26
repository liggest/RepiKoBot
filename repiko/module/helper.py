
from pathlib import Path

from LSparser.command.helper import CommandHelper

from repiko.module.img.typ import typ_file2png, default_font_paths

class RpkHelper(CommandHelper):
    def __init__(self, root: Path | str = Path("./help"), core=None):
        super().__init__(root, core)

    @property
    def rootPath(self) -> str:
        # 兼容旧逻辑
        return self._rootPath.as_posix()

    @rootPath.setter
    def rootPath(self, value: Path | str):
        self._rootPath = Path(value)
    
    def getHelpToml(self, target: str | list = ""):
        """
            按页查看指令对应的帮助 toml 文件\n
                target 目标指令，可以为字符串或列表，内容为指令名或包含其下的选项名\n
        """
        cmd, target = self.tryFindCmd(target) # 检查、更新target，并尝试寻找指令模板
        filePath = self.getHelpFilePath(target, ".toml") or self.getHelpFilePath(target, ".typ")
        if filePath:
            return filePath
        return None

    def getHelpFilePath(self, target:list, suffix=".txt"):
        path = self._rootPath.joinpath(*target)
        filePath = path.with_suffix(suffix) # 先找 name.{suffix}
        if not filePath.exists():
            filePath = (path / self.defaultFile).with_suffix(suffix) # 再找 name/general.{suffix}
            if not filePath.exists():
                return None
        return filePath
    
def renderHelpToml(filePath: Path, ppi: float = 144):
    if filePath.suffix == ".toml":
        data = {"content": (Path("/") / filePath).as_posix()}
        filePath =  Path("typ/template/help_temp.typ")
    elif filePath.suffix == ".typ":
        data = {}
    return typ_file2png(filePath, default_font_paths(), root=Path("."), ppi=ppi, data=data)
