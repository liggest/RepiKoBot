import asyncio
import typing
from unittest import result
import httpx
import itertools
from collections import deque
from pathlib import Path

from LSparser import *

from repiko.core.bot import Bot
from repiko.core.constant import MessageType,EventNames
from repiko.msg.part import Image
from repiko.msg.data import Message

from repiko.module.str2image import str2greyPng

ygopath:Path=None
deckpath:Path=None
deckext=".ydk"

Command("decks")
Command("deckset").names("setdeck","设置卡组").opt("-me",OPT.N,"自己的卡组")
Command("deckdel").names("deldeck","删除卡组")

@Events.onCmd("deckset")
async def deckset(pr:ParseResult):
    msg:Message=pr.raw
    if msg.mtype!=MessageType.Group:
        return ["现在只支持在群聊中上传卡组…"]
    bot:Bot=msg.selector.bot
    paths=[Path(para) for para in pr.params if str(para).strip()]
    if not paths:
        return ["倒是指定一些卡组文件呀！"]
    # path="/".join([para for para in pr.params if str(para).strip()])
    # path=Path(path)
    # gFile=await bot.GroupFileInfo(msg.src,path)
    asyncio.create_task(downloadTask(bot,msg.src,paths,msg.realSrc if pr["me"] else False ))

async def downloadTask(bot:Bot,group:int,paths:typing.List[Path],me:int=False):
    result=[]
    for path in paths:
        file=await bot.GroupFileInfo(group,path)
        if not file and not path.suffix and path.name:
            path=path.with_suffix(deckext)
            file=await bot.GroupFileInfo(group,path)
        if not file:
            result.append(f"没找到 {path.as_posix()} … 真的在群里吗？")
        elif "file_id" in file:
            if not me or str(file["uploader"])==str(me):
                result.append(await downloadFile(bot,group,file,path))
        elif "folder_id" in file or "files" in file: # 包括 root{files,folders}的情况
            folder=file
            if "folder_id" in file:
                folder=await bot.GroupSubFolder(group,file["folder_id"])
                if not folder:
                    result.append(f"没找到 {path.as_posix()} 目录… 真的在群里吗？")
                    continue
            files=folder["files"]
            if not files:
                result.append(f"{path.as_posix()} 目录里没有文件啊！？")
            else:
                for file in files:
                    if not me or str(file["uploader"])==str(me):
                        result.append(await downloadFile(bot,group,file,path/file["file_name"]))
    if result:
        await bot.AsyncSend(Message.build("\n".join(result),group,MessageType.Group))
    

async def downloadFile(bot:Bot,group:int,file:dict,path:Path):
    name:str=file["file_name"]
    if not name.endswith(deckext):
        return f"{path.as_posix()} 非卡组文件，已忽略"
    fileLink=await bot.GroupFileLink(group,file)
    if not fileLink:
        return f"没找到 {path.as_posix()} … 真的在群里吗？"
    try:
        async with httpx.AsyncClient() as client:
            res=await client.get(fileLink)
            deckfile:Path=deckpath / file["file_name"]
            uploader=await bot.GroupMemberInfo(group,file["uploader"])
            if uploader and uploader.get("card"):
                deckfile=deckpath / f"{deckfile.stem}_by_{uploader['card']}{deckfile.suffix}"
            else:
                deckfile=deckpath / f"{deckfile.stem}_by_{file['uploader_name']}{deckfile.suffix}"
            with open(deckfile,"wb") as f:
                f.write(res.content)
        if not checkDeck(deckfile):
            deckfile.unlink()
            return f"{path.as_posix()} 里卡的数量好像不太够呀…？"
        return f"耶！已下载 {path.as_posix()}"
    except:
        return f"下载 {path.as_posix()} 失败！？明明就差一点了……"

def checkDeck(deckfile:Path):
    main=deque(maxlen=60)
    extra=deque(maxlen=15)
    side=deque(maxlen=15)
    current="start"
    with deckfile.open("r",encoding="utf-8") as f:
        for line in f:
            if line.startswith("#main"):
                current="main"
                continue
            elif line.startswith("#extra"):
                current="extra"
                continue
            elif line.startswith("!side"):
                current="side"
                continue
            elif current=="main":
                main.append(line.strip())
            elif current=="extra":
                extra.append(line.strip())
            elif current=="side":
                side.append(line.strip())
    if len(main)<40:
        return False
    return True
        
@Events.onCmd("decks")
def decks(pr:ParseResult):
    params=[para for para in pr.params if str(para).strip()]
    files=(Path(file.name) for file in deckpath.iterdir())
    if params:
        files=filter(lambda file: file.suffix.endswith(deckext) and any(filter(file.match,params)),files)
    else:
        files=filter(lambda file: file.suffix.endswith(deckext),files)
    path=str2greyPng(itertools.chain(("卡组列表",),files),None,overwrite=True)
    return [Image(path,cache=False)]

@Events.onCmd("deckdel")
async def deckdel(pr:ParseResult):
    msg:Message=pr.raw
    bot:Bot=msg.selector.bot
    result=[]
    for path in pr.params:
        if not str(path).strip():
            continue
        name=Path(path).with_suffix(deckext)
        path=deckpath / name.name
        if path.is_file():
            path.unlink()
        else:
            name=name.with_name(f"{name.stem}_by_{msg.getSrcCard()}{name.suffix}")
            path=deckpath / name.name
            if path.is_file():
                path.unlink()
            else:
                result.append(f"删除 {name.name} 失败…或许根本没有这个卡组？")
                continue
        result.append(f"删除 {name.name}…")
    if result:
        return ["\n".join(result)]
    else:
        return ["倒是指定一些卡组文件呀！"]

def initDeck(bot:Bot):
    global ygopath,deckpath
    ygopath=Path(bot.config["ygo"]["ygoPath"])
    deckpath=ygopath / "deck" / "random"
    deckpath.mkdir(0o774,parents=True,exist_ok=True)
    print(f"确保 {deckpath} 存在")

@Events.on(EventNames.StartUp)
def botStartUP(bot:Bot):
   initDeck(bot)