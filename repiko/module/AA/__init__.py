
from AA.file import AAFile
from AA.AAMZ import AAMZ
from AA.AAHub import AAHub
from AA.backend import Backend

class _BackendToUse:

    defaultName = "AAMZ"
    current:Backend[AAFile] = None

    backends:dict[str, type[Backend[AAFile]]] = {}

    @classmethod
    def _backendName(cls, _backend: Backend | type[Backend] | str | None):
        if _backend is None:
            return cls._toName(cls.defaultName)
        if isinstance(_backend, str):
            return cls._toName(_backend)
        if isinstance(_backend, Backend):
            return cls._toName(_backend.__class__.__name__)
        return cls._toName(_backend.__name__)

    @staticmethod
    def _toName(name: str):
        return name.lower()
    
    @classmethod
    def fromName(cls, name: str = None):
        backendName = cls._backendName(name)
        if cls.current and backendName == cls._backendName(cls.current):
            return cls.current
        
        backendCls = cls.backends.get(backendName)
        
        if backendCls is None:
            raise ValueError(f'Unknown site: {name}')
        cls.current = backendCls()
        print(f"将使用 {name} 站点里的 AA")
        return cls.current

_BackendToUse.backends = {
    _BackendToUse._backendName(AAMZ) : AAMZ ,
    _BackendToUse._backendName(AAHub): AAHub,
}

def isSite(siteName:str=None):
    return siteName is None or _BackendToUse._toName(siteName) in _BackendToUse.backends

def hasInited() -> bool:
    return _BackendToUse.current and _BackendToUse.current.files

async def init(siteName:str=None):
    aa = _BackendToUse.fromName(siteName)
    await aa.init()

async def randomAA(siteName:str=None, hasR18=False):
    aa = _BackendToUse.fromName(siteName)
    return await aa.randomAA(hasR18)
