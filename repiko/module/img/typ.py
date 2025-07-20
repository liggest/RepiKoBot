from pathlib import Path
from tempfile import NamedTemporaryFile

import typst

def default_root_path():
    return Path("typ")

def default_font_paths():
    return [Path("font")]

def default_template_path():
    return default_root_path() / "template"

def typ_str2png(text: str, font_paths: list[Path] | None = None, root: Path | None = None, ppi:float=144, data: dict[str, str] | None = None):
    root = root or default_root_path()
    with NamedTemporaryFile(suffix=".typ", dir=root.as_posix()) as f:
        f.write(text.encode("utf-8"))
        f.flush()
        path = root / f.name
        return typ_file2png(path, root, font_paths, ppi, data)

def typ_file2png(path: Path, font_paths: list[Path] | None = None, root: Path | None = None, ppi:float=144, data: dict[str, str] | None = None):
    return typst.compile(path, output=None, root=root,
        font_paths=font_paths or [], ignore_system_fonts=font_paths is not None, 
        format="png", ppi=ppi, 
        sys_inputs=data or {}
    )
