from __future__ import annotations

import asyncio

from typing import Coroutine # , TYPE_CHECKING

# from repiko.core.constant import PostType
from repiko.core.log import logger

# if TYPE_CHECKING:
#     from repiko.msg.data import BaseData
#     from repiko.core.bot import Bot

_tasks=set()

def _on_done(task:asyncio.Task):
    _tasks.discard(task)
    if e:=task.exception():
        logger.opt(exception=e).exception(f"{task} 运行时出错：")

def createTask(coro:Coroutine,**kw):
    """
        包装了 asyncio.create_task\n
        使要执行的任务在完成前不会被意外地垃圾回收\n
        执行出错时由 logger 报告错误信息
    """
    task=asyncio.create_task(coro,**kw)
    _tasks.add(task)
    task.add_done_callback(_on_done)
    return task


# async def _botHandle(bot:Bot,rj:dict):
#     postType=rj["post_type"]
#     #DEBUG
#     if bot.DebugMode and postType!=PostType.Meta: #不打印心跳
#         logger.debug(rj)
    
#     sltr=None
#     if any(sltr:=s for s in bot.selectors if s.isAccept(rj)):
#         msg:BaseData=await sltr.asyncAction(rj)
#         sltr.runBackTasks()
#         if msg and msg.quickReply: # 快速操作
#             logger.info(f"quickReply:{msg.replyJson}")
#             return msg.replyJson
#     return {}
