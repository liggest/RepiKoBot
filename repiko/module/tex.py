import httpx
from PIL import ImageFont, Image
# from svglib.svglib import svg2rlg,register_font
# from reportlab.graphics import renderPM
from bs4 import BeautifulSoup
from bs4.element import Tag
# from io import StringIO,BytesIO
from io import BytesIO
from pathlib import Path
# from reportlab import rl_settings
# rl_settings.renderPMBackend="rlPyCairo"
from resvg_py import svg_to_bytes

# try:
#     import rlPyCairo
#     HASrlPyCairo=True
# except:
#     HASrlPyCairo=False

# from reportlab import rl_config
# rl_config.autoGenerateTTFMissingTTFName=True
# reportlab 注册字体时好像用到了这个属性，明明 rl_settings 里面有…但改那边的却没用


# from cairosvg import svg2png
# import PIL.Image as PILImage

from repiko.module.str2image import getSize

fontName: str = None
fontPath: str = None
fontSize = 15
font: ImageFont.FreeTypeFont = None
ex2px: int = None

url = r"https://www.zhihu.com/equation"


class LatexError(ValueError):
    pass

def register_font(name: str, path: str):
    global fontName, fontPath, font, ex2px
    fontPath = path
    font = ImageFont.truetype(fontPath, fontSize)
    ex2px = getSize(font, "x")[1]
    fontName, fontStyle = font.getname()
    return name, True

def initFont(path: str):
    # TODO Font Manager
    if not (path and Path(path).exists()):
        return print(f"字体 {path} 未找到！")
    name = Path(path).stem.split()[0]
    name, success = register_font(name, path)
    print(f"注册字体 {name}")
    if not success:
        raise ValueError("字体路径有误！")
    # fontName=name
    # fontPath=path
    # font=ImageFont.truetype(fontPath,fontSize)
    # ex2px = getSize(font, "x")[1]

def tex2img(tex: str):
    if not font:
        raise ValueError("还没有字体！")
    svgText = httpx.get(url, params={"tex": tex}).text
    root = reviseSVG(svgText)
    # img=svg2img(root.text)
    # return img2bytes(img)
    return svg2bytes(root.text)


async def atext2img(tex: str):
    if not font:
        raise ValueError("还没有字体！")
    async with httpx.AsyncClient() as client:
        client: httpx.AsyncClient
        svgText = (await client.get(url, params={"tex": tex})).text
    root = reviseSVG(svgText)
    # img=svg2img(str(root))
    # return img2bytes(img)
    return svg2bytes(str(root))


def reviseSVG(svgText: str):
    global font, ex2px, fontSize
    root = BeautifulSoup(svgText, "lxml-xml")
    svg: Tag = root.contents[0]
    errorNode = svg.find("rect", {"fill": "rgba(247, 86, 89, 0.08)"})
    if errorNode:
        errorText = errorNode.parent.find("text")
        raise LatexError(errorText.string if errorText else "Unknown Error")
    svg["width"] = ex2pxStr(svg.get("width"))
    svg["height"] = ex2pxStr(svg.get("height"))
    for style in root.get("style", "").split(";"):
        if style.startswith("font-size:"):
            # 除去头部的 font-size: 和 尾部的 px，得到字体大小 len("font-size:")=10 len("px")=2
            fontSize = int(style[10:-2].strip())
            font = ImageFont.truetype(fontPath, fontSize)
            ex2px = getSize(font, "x")[1]
            break
    # fontFamily=f"font-family: {fontName}, monospace;"
    # if HASrlPyCairo:
    #     fontStyle=f"font-family: {fontName}, monospace; font-size: {fontSize-1}px;"
    # else:
    #     fontStyle=f"font-family: {fontName}; font-size: {fontSize-1}px;" # 字号也稍微小一点，好像只影响中文
    fontStyle = f"font-family: {fontName}, monospace; font-size: {fontSize-1}px;"
    for node in svg.find_all(attrs={"font-family": "monospace"}):
        node: Tag
        s = node.string
        # if s.startswith("Undefined control sequence"):
        #     raise LatexError(s)
        if not s.isascii():
            del node["font-family"]
            style = node.get("style", "")
            node["style"] = f"{fontStyle} {style}"

    # def removeXlinks(node:Tag):
    #     xlinks=[attr for attr in node.attrs if attr.startswith(("xlink","xmlns"))]
    #     if xlinks:
    #         for x in xlinks:
    #             del node[x]

    # for node in svg.parent.find_all(removeXlinks):
    #     pass
    return svg

def ex2pxStr(s: str):
    if s and s.endswith("ex"):
        width = float(s[:-2])  # 除去 ex
        width *= ex2px
        return f"{width}px"
    return s

def svg2img(svgText: str):
    # svgDraw=svg2rlg(StringIO(svgText))
    # if HASrlPyCairo:
    #     img:Image=renderPM.drawToPIL(svgDraw,backend='rlPyCairo')
    # else:
    #     img:Image=renderPM.drawToPIL(svgDraw)
    raw = svg_to_bytes(svg_string=svgText, dpi=144, font_files=[fontPath])
    img = Image.open(BytesIO(bytes(raw)), formats=("PNG",))
    # print(svgText)
    # bio=BytesIO()
    # svg2png(file_obj=StringIO(svgText),write_to="a.png",background_color="transparent")
    # img=PILImage.open(bio)
    return img

def img2bytes(img: Image.Image):
    with BytesIO() as byts:
        img.save(byts, "PNG")
        return byts.getvalue()

def svg2bytes(svgText: str):
    # print(repr(svgText))
    # print(repr(fontPath))
    return bytes(svg_to_bytes(svg_string=svgText, dpi=144, font_files=[fontPath]))


if __name__ == "__main__":
    import asyncio
    from pathlib import Path

    async def main():
        fontPaths = [*Path("font").glob("*.tt?")]
        for i, path in enumerate(fontPaths):
            print(f"{i}. {path}")
        path = fontPaths[int(input("选："))]
        initFont(str(path))
        texStr = input("tex:")
        while texStr:
            img = Image.open(BytesIO(await atext2img(texStr)), formats=("PNG",))
            img.show()
            texStr = input("tex:")

    asyncio.run(main())
