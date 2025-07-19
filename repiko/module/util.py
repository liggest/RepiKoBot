from contextlib import asynccontextmanager

from repiko.msg.part import Share as _Share, Text, Image
from repiko.msg.data import Message
from repiko.core.constant import MessageType
from repiko.core.bot import Bot

from LSparser import ParseResult

CONS=None
def redirect(cmd:str,pattern=None,func:callable=None):
    def onRedirect(pr:ParseResult):
        pr=modifyResult(pr,cmd,pattern)
        if func:
            return func(pr)
    return onRedirect

def asyncRedirect(cmd:str,pattern=None,func:callable=None):
    async def onRedirect(pr:ParseResult):
        pr=modifyResult(pr,cmd,pattern)
        if func:
            return await func(pr)
    return onRedirect

def modifyResult(pr:ParseResult,cmd:str,pattern:list=None):
    pr.command=cmd
    pr._cons[0]=f"{pr.type}{pr.command}"
    if pattern:
        cons=[]
        for p in pattern:
            if p is CONS:
                cons+=pr._cons[1:]
            elif isinstance(p,list):
                cons+=p
            else:
                cons.append(p)
        pr._cons=pr._cons[:1]+cons
    pr=pr.parser._parserCore.command2obj(pr,pr.parser)
    pr.params=[]
    pr=pr.parse()
    return pr


class Share:

    def __init__(self,url:str,title:str="",content:str=None,imageUrl:str=None,mtype=MessageType.Private,**kw):
        self.share=_Share(url,title,content,imageUrl,**kw)
        self.mtype=mtype
    
    def to(self,tar):
        if isinstance(tar,ParseResult):
            tar:Message=tar.raw
            self.mtype=tar.mtype
        elif isinstance(tar,Message):
            self.mtype=tar.mtype
        elif tar in MessageType:
            self.mtype=tar
        if self.mtype==MessageType.Group:
            return Text(self.share.url)
        return self.share
    
def images_gen(data: bytes | list[bytes]):
    if isinstance(data, bytes):
        yield Image(data)
    else:
        for d in data:
            yield Image(d)

@asynccontextmanager
async def under_emoji(bot: Bot, message_id: int, emoji_id: int, cancel_later=True):
    try:
        yield await bot.PasteEmoji(message_id, emoji_id)
    finally:
        if cancel_later:
            await bot.PasteEmoji(message_id, emoji_id, paste=False)

async def under_emoji_pr(pr:ParseResult, emoji_id: int, cancel_later=True):
    msg: Message = pr.raw
    return under_emoji(msg.selector.bot, msg.id, emoji_id, cancel_later)
