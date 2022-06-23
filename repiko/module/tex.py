import httpx
from PIL import ImageFont
from PIL.Image import Image
from svglib.svglib import svg2rlg,register_font
from reportlab.graphics import renderPM
from bs4 import BeautifulSoup
from bs4.element import Tag
from io import StringIO,BytesIO

fontName:str=None
fontPath:str=None
fontSize=15
font:ImageFont.FreeTypeFont=None
ex2px:int=None

url=r"https://www.zhihu.com/equation"

class LatexError(ValueError):
    pass

def initFont(name:str,path:str):
    # TODO Font Manager
    global fontName,fontPath,font,ex2px
    name,success=register_font(name,path)
    print(f"注册字体 {name}")
    if not success:
        raise ValueError("字体路径有误！")
    fontName=name
    fontPath=path
    font=ImageFont.truetype(fontPath,fontSize)
    ex2px=font.getsize("x")[1]

def tex2img(tex:str):
    if not font:
        raise ValueError("还没有字体！")
    svgText=httpx.get(url,params={"tex":tex}).text
    root=reviseSVG(svgText)
    img=svg2img(root.text)
    return img2bytes(img)
    
async def atext2img(tex:str):
    if not font:
        raise ValueError("还没有字体！")
    async with httpx.AsyncClient() as client:
        client:httpx.AsyncClient
        svgText=(await client.get(url,params={"tex":tex})).text
    root=reviseSVG(svgText)
    img=svg2img(str(root))
    return img2bytes(img)

def reviseSVG(svgText:str):
    global font,ex2px,fontSize
    root=BeautifulSoup(svgText,"lxml-xml")
    svg:Tag=root.contents[0]
    svg["width"]=ex2pxStr(svg.get("width"))
    svg["height"]=ex2pxStr(svg.get("height"))
    for style in root.get("style","").split(";"):
        if style.startswith("font-size:"):
            # 除去头部的 font-size: 和 尾部的 px，得到字体大小 len("font-size:")=10 len("px")=2
            fontSize=int(style[10:-2].strip())
            font=ImageFont.truetype(fontPath,fontSize)
            ex2px=font.getsize("x")[1]
            break
    # fontFamily=f"font-family: {fontName}, monospace;"
    fontFamily=f"font-family: {fontName};"
    for node in svg.find_all(attrs={"font-family":"monospace"}):
        node:Tag
        s=node.string
        if s.startswith("Undefined control sequence"):
            raise LatexError(s)
        if not s.isascii():
            del node["font-family"]
            style=node.get("style","")
            node["style"]=f"{fontFamily} {style}"
    return svg

def ex2pxStr(s:str):
    if s and s.endswith("ex"):
        width=float(s[:-2]) #除去 ex
        width*=ex2px
        return f"{width}px"
    return s

def svg2img(svgText:str) -> Image:
    svgDraw=svg2rlg(StringIO(svgText))
    img:Image=renderPM.drawToPIL(svgDraw)
    return img

def img2bytes(img:Image):
    with BytesIO() as byts:
        img.save(byts, 'PNG')
        return byts.getvalue()