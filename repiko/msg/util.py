import re
import os
import base64
import pathlib

_escapeMap={
    "&":"&amp;",
    "[":"&#91;",
    "]":"&#93;",
    ",":"&#44;"
}
_unescapeMap={v:k for k,v in _escapeMap.items()}

_escapePtn=re.compile(r"[&\[\]]")
_escapeCommaPtn=re.compile(r"[&\[\],]") # 多个逗号

_unescapePtn=re.compile(r"(&amp;|&#91;|&#93;)")
_unescapeCommaPtn=re.compile(r"(&amp;|&#91;|&#93;|&#44;)")

_CQcodePtn=re.compile(r"(&amp;|&#91;|&#93;|&#44;|\[CQ:)")

def _escapeSub(m:re.Match) -> str:
    return _escapeMap[m.group()]

def _unescapeSub(m:re.Match) -> str:
    return _unescapeMap[m.group()]

def CQescape(s:str):
    """ 转义CQ码（不带逗号） """
    return re.sub(_escapePtn,_escapeSub,s)

def CQescapeComma(s:str):
    """ 转义CQ码（带逗号） """
    return re.sub(_escapeCommaPtn,_escapeSub,s)

def CQunescape(s:str):
    """ 反转义CQ码（不带逗号） """
    return re.sub(_unescapePtn,_unescapeSub,s)

def CQunescapeComma(s:str):
    """ 反转义CQ码（带逗号） """
    return re.sub(_unescapeCommaPtn,_unescapeSub,s)

def isCQcode(s):
    if isinstance(s,str):
        return re.search(_CQcodePtn,s)
    return False

def dictSetter(key):
    """ 生成属性的 setter 函数，为字典(self)的指定键 key 赋值 """
    def setter(self,val):
        self[key]=val
    return setter

def readBytes(path:str):
    """ 以字节串的形式读取文件 """
    bts=None
    with open(path,"rb") as f:
        bts=f.read()
    return bts

def fileUrl(path:str):
    return f"file:///{path}"

def b64Url(bts:bytes):
    return f"base64://{base64.b64encode(bts).decode()}"

def dealFile(file):
    if isinstance(file,str) and os.path.isfile(file):
        return fileUrl(os.path.abspath(file).lstrip('/'))
    elif isinstance(file,pathlib.Path):
        return fileUrl(file.resolve())
    elif isinstance(file,bytes):
        return b64Url(file)
    return file