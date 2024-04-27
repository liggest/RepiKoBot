from PIL import Image,ImageDraw,ImageFont
import os
import typing
# import textwrap

marginSize=(20,20)
standardWidth=640
# titleFont=ImageFont.truetype(r"font/PingFang Regular.ttf",24) #总之需要一个字体
titleFont:ImageFont.FreeTypeFont=None
titleSpacing=3
titleXY=(marginSize[0]//2,marginSize[1]//2)
# font=ImageFont.truetype(r"font/PingFang Regular.ttf",16)
font:ImageFont.FreeTypeFont=None
spacing=2
lineHeight:int=None
imageDir=r"image/"
if not os.path.exists(imageDir):
    os.makedirs(imageDir)

def getSize(font: ImageFont.FreeTypeFont, text: str, *args, **kw):
    bbox = font.getbbox(text, *args, **kw)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def initFont(path:str):
    global titleFont,font,lineHeight
    if not (path and os.path.exists(path)):
        return print(f"字体 {path} 未找到！")
    titleFont=ImageFont.truetype(path,24) #总之需要一个字体
    font=ImageFont.truetype(path,16)
    lineHeight=getSize(font, "A")[1]


def getFileName(title:str,fileName,suffix=".png"):
    if fileName is None:
        if title.strip()=="":
            fileName="noName"
        else:
            fileName=title
    if fileName.endswith(suffix):
        return fileName
    else:
        return fileName+suffix

def getFilePath(title,fileName,suffix=".png"):
    return imageDir+getFileName(title,fileName,suffix)

def str2greyPng(text:typing.Union[str,typing.Iterable],fileName=None,overwrite=False):
    if isinstance(text,str):
        lines=text.splitlines()
    elif isinstance(text,typing.Iterable):
        lines=[*map(str,text)]
    title=""
    if lines:
        title=lines[0]
    # fileName=getFileName(title,fileName)
    filePath=getFilePath(title,fileName)
    if imageExists(filePath) and not overwrite:
        return r"file:///"+os.path.abspath(filePath).lstrip("/")
    img=drawText(title,lines[1:])
    img.save(filePath)
    return r"file:///"+os.path.abspath(filePath).lstrip("/")

def drawText(title,lines): #这里的lines不包括title
    if not titleFont or not font:
        raise ValueError("还没有字体！")
    titleSize=getSize(titleFont, title)
    maxWidth=max(standardWidth,titleSize[0])
    height=titleSize[1]+titleSpacing
    maxTextWidth=titleSize[0]
    for i,line in enumerate(lines):
        line,lineSize=splitLine(line,maxWidth)
        height+=lineSize[1]+spacing
        maxTextWidth=max(lineSize[0],maxTextWidth)
        lines[i]=line
    height-=spacing
    width=min(maxTextWidth,maxWidth)
    size=(marginSize[0]+width,marginSize[1]+height)
    img=Image.new("L",size,244) #灰度图像
    draw=ImageDraw.Draw(img)
    draw.font=titleFont
    draw.text(titleXY,title,fill=64,spacing=titleSpacing) # 第一个参数为 xy 坐标
    draw.font=font
    draw.multiline_text( (titleXY[0],titleXY[1]+titleSize[1]+spacing),"\n".join(lines),fill=64,spacing=spacing) # 第一个参数为 xy 坐标
    return img

def splitLine(line,maxWidth):
    if not font:
        raise ValueError("还没有字体！")
    lineSize=list(getSize(font, line))
    lineSize[1]=lineHeight
    if lineSize[0]<=maxWidth:
        return line,tuple(lineSize)
    else:
        left=0
        right=len(line)
        current=(left+right)//2
        currentLine=line
        while left<right and right-left>1: #找到最合适的字数
            current=(left+right)//2
            currentLine=line[:current]
            currentSize=getSize(font, currentLine)
            if currentSize[0]<maxWidth:
                left=current
            elif currentSize[0]>maxWidth:
                right=current
            else:
                left=current
                break
        currentLine=line[:left]
        currentSize=getSize(font, currentLine)
        otherLine,otherSize=splitLine(line[left:],maxWidth)
        lineSize[1]+=otherSize[1]+spacing
        lineSize[0]=max(currentSize[0],otherSize[0])
        return currentLine+"\n"+otherLine,tuple(lineSize)

def imageExists(fileName):
    return os.path.exists(fileName)



