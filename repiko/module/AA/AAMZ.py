import httpx
from contextvars import ContextVar
from repiko.module.AA.file import AAFile
import random
import html
# from pprint import pprint

# header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',"Content-Type": "application/json"}

baseUrl=r"https://aa.yaruyomi.com/"
metaUrl=r"api/events/url"
listUrl=None
contentUrl=None

files=[]

# url=r"https://aa.yaruyomi.com/api/matome-zip/comp/file/list"
# url=r"https://aa.yaruyomi.com/api/events/url"
# url=r"https://aa.yaruyomi.com/api/matome-zip/file/contents"

clientVar=ContextVar("client",default=None)

async def httpRequest(url,param=None):
    client:httpx.AsyncClient=clientVar.get()
    if client:
        r=await client.get(url,params=param,timeout=180)
        return r.json()

async def getUrls():
    global listUrl,contentUrl
    rj=await httpRequest(f"{baseUrl}{metaUrl}")
    if rj:
        listUrl=rj["events"]["matomeCompFileList"]
        contentUrl=rj["events"]["matomeFileContents"]
        return True

async def getFileList():
    if listUrl or await getUrls():
        rj=await httpRequest(listUrl)
        if rj:
            return [AAFile(f) for f in rj]
    return []

async def getFileContent(file:AAFile):
    if contentUrl or await getUrls():
        rj=await httpRequest(contentUrl,param={"hash":file.hash})
        if rj:
            if "contents" in rj:
                rj["contents"]=[ html.unescape(c).replace("\r\n","\n") for c in rj["contents"] ]
            return AAFile(rj)

async def init():
    global files
    async with httpx.AsyncClient() as client:
        clientVar.set(client)
        if not files:
            files=await getFileList()
            print(f"读取到了 {len(files)} 个 AA 文件")

async def randomFile():
    if not files:
        return None
    l=len(files)
    idx=random.randint(0,l-1)
    file=files[idx]
    if not file.hasContents:
        async with httpx.AsyncClient() as client:
            clientVar.set(client)
            file=await getFileContent(file)
        if not file:
            return None
        file.save()
    return file
    
def chooseContents(file:AAFile,hasR18=False):
    if ("R18" in file.name or "R18" in file.dir) and not hasR18:
        return

    picked=[]
    for c in file.contents:
        cs=c.strip(" \n\r")
        if "R18" in cs:
            if not hasR18:
                break
            continue
        if cs.startswith("最終更新日"): # 最终更新日 xxx
            continue
        if cs.startswith("【") and cs.endswith("】"): # 【xxx】
            continue
        if not "\n" in cs: # 没有换行
            continue
        picked.append(c)

    if picked:
        return random.choice(picked)

async def randomAA(hasR18=False):
    AAtext=None
    file=None
    while not AAtext:
        file=await randomFile()
        if file:
            AAtext=chooseContents(file,hasR18)
    return AAtext,file