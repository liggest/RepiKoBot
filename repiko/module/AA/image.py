from PIL import Image,ImageDraw,ImageFont
from pathlib import Path

imsize=(20,20)
# font=ImageFont.truetype(r"font/MS PGothic.ttf",16)
font:ImageFont.FreeTypeFont=None

def initFont(path:str):
    global font
    if not (path and Path(path).exists()):
        return print(f"字体 {path} 未找到！")
    font=ImageFont.truetype(path,16) #总之需要一个字体

def AA2img(AAtext:str):
    if not font:
        raise ValueError("还没有 AA 字体！")
    AAsize=font.getsize_multiline(AAtext,spacing=2)
    size=( imsize[0]+AAsize[0],imsize[1]+AAsize[1] )
    img=Image.new("RGB",size,(244,244,244))
    draw=ImageDraw.Draw(img)
    draw.font=font
    draw.multiline_text((10,10),AAtext,fill=(64,64,64),spacing=2)
    return img
