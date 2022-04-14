from LSparser import Events

from repiko.core.bot import Bot
from repiko.core.constant import EventNames,MessageType
from repiko.msg.data import Message
from repiko.msg.part import Face,Reply

import asyncio

@Events.on(EventNames.AtMe)
async def atMe(msg:Message,bot:Bot):
    # raw=msg
    if not isinstance(msg,str):
        content=msg.content.plainText
    if "是不是" in content:
        return "围观群众：是啊是啊"
    elif "生气了" in content:
        return "没有哦"
    elif "草" in content or "艹" in content:
        return msg.content
    elif "嘤" in content:
        return "我一拳打死一个嘤嘤怪"
    elif "哥" in content or "弟" in content:
        return "欧尼酱~"
    elif "姐" in content or "妹" in content:
        return "欧内酱~"
    elif content.strip()=="弱人工智能" or content.strip()=="鶸人工智能":
        return "你们阉太监也不会动人脑子！"
    elif "来一句" in content or "说一句" in content or "来句话" in content:
        return await bot.plugins["basic"].aword(None)
    else:
        return "不要碰我呀QwQ"

scaredWords=[Face(55),Face(146),"多嘴","住口","住嘴","撤回"]

async def delayedDelete(bot:Bot,msgID:int,second:int=8):
    await asyncio.sleep(second)
    await bot.DeleteMsg(msgID)

@Events.on(EventNames.ReplyMe)
async def replyMe(msg:Message,bot:Bot):
    content=msg.content
    reply:Reply=content[0]
    for word in scaredWords:
        if word in content:
            # deleteMine=asyncio.create_task(bot.DeleteMsg(reply.id))
            await bot.DeleteMsg(reply.id)
            if msg.mtype==MessageType.Group:
                meInGroup=await bot.GroupMemberInfo(msg.src,bot.MYQQ)
                # print(meInGroup)
                myRole=meInGroup.get("role",None)
                if myRole=="owner" or myRole=="admin":
                    bot.AddBackTask(delayedDelete,bot,msg.id)
                    # await asyncio.sleep(10)
                    # await bot.DeleteMsg(msg.id)
                    # print("应该撤回？")
            # await deleteMine
            break

