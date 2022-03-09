from PIL import Image,ImageDraw,ImageFont

imsize=(20,20)
font=ImageFont.truetype(r"font/MS PGothic.ttf",16)

def AA2img(AAtext:str):
    AAsize=font.getsize_multiline(AAtext,spacing=2)
    size=( imsize[0]+AAsize[0],imsize[1]+AAsize[1] )
    img=Image.new("RGB",size,(244,244,244))
    draw=ImageDraw.Draw(img)
    draw.font=font
    draw.multiline_text((10,10),AAtext,fill=(64,64,64),spacing=2)
    return img