#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI,Request,Depends,BackgroundTasks

# import random
# import json
# import typing

from repiko.core.constant import PostType
from repiko.core.bot import Bot
from repiko.msg.data import BaseData
# from repiko.msg.selector import *
# from repiko.msg.message import Message

app=FastAPI()

bot:Bot=None

@app.on_event("startup")
async def StartUp():
    global bot
    # import repiko.core.bot as bot_core
    # bot=bot_core.Bot()
    bot=Bot()
    await bot.Init()

@app.on_event("shutdown")
async def ShutDown():
    await bot.Shutdown()

@app.post("/",response_model=None)
async def MessageReceiver(backTasks:BackgroundTasks,request:Request):
    rd=await request.body()
    if bot.Verification(request,rd):
        rj=await request.json()
        postType=rj["post_type"]

        #DEBUG
        if bot.DebugMode and postType!=PostType.Meta: #不打印心跳
            print(rj)
        
        sltr=None
        for s in bot.selectors:
            if s.isAccept(rj):
                sltr=s
                break
        if sltr:
            msg:BaseData=await sltr.asyncAction(rj,backTasks)
            print(msg)
            print(repr(msg.content))
            if msg and msg.quickReply: #快速操作
                print("quickReply",msg.replyJson)
                return msg.replyJson
    return {}

#============#
# Old Stuffs #
#============#

# from flask import Flask,request
# from werkzeug.serving import is_running_from_reloader

# app = Flask(__name__)
# if not is_running_from_reloader():
#     import repiko.core.bot as bot_core
#     bot=bot_core.Bot()

# @app.route('/',methods=['POST'])
# def MessageReceiver():

async def get_body(request: Request):
    await request.json()
    return request

# @app.post("/",response_model=None)
def __MessageReceiver(backTasks:BackgroundTasks,request:Request=Depends(get_body)): #暂时的异步->同步对策
    # rd=request.get_data()
    # rd=await request.body()
    # if not hasattr(request,"_body"):
    #     return {}
    rd=request._body
    if bot.Verification(request,rd):
        # rj=json.loads(rd)
        #request.get_data(as_text=True)
        # rj=await request.json()
        rj=request._json
        postType=rj["post_type"]

        #DEBUG
        # if bot.DebugMode:
        if bot.DebugMode and postType!=PostType.Meta:
            #不打印心跳
            print(rj)
        
        # if postType!=PostType.Meta:
        #     import time
        #     time.sleep(5)

        sltr=None
        for s in bot.selectors:
            if s.isAccept(postType):
                sltr=s 
                break
        if sltr:
            msg=sltr.action(rj,backTasks)
            if msg and msg.quickResponse: #快速操作
                print("quickResponse",msg.resj)
                # return json.dumps(msg.resj)
                return msg.resj
        
        #回复相关
        # if postType=="message":
            # response=False
            # responseMsg=""
            # atSender=True
            # #基础信息
            # msg=Message.fromJSON(rj)
            # msgType=rj["message_type"]
            # contents=rj["message"]
            # msgID=rj["message_id"]
            # 希望能更灵活的得到回复QQ
            # rq=bot.GetReceiveQQ(rj,msgType)
            # #复读 2%几率复读1次 2‰几率复读3次
            # temp=random.randint(1,1000)
            # if temp>=500 and temp<520:
            #     # msg.srcAsDst()
            #     bot.SendMessage(msg.srcAsDst())
            #     # bot.SendMessage(msgType,rq[0],contents)
            # elif temp==1 or temp==1000:
            #     # msg.srcAsDst()
            #     bot.SendMsgList([msg.srcAsDst()]*3)
            #     # bot.SendMsgList(msgType,rq[0],[contents]*3)
            #管理
            # if rq[-1] in bot.AdminQQ:
            # if msg.realSrc in bot.AdminQQ:
            #     if msg.content.startswith("-"):
            #         adminr=bot.ac.GetAdminResponse(msg.content)
            #         bot.SendStrList(msg.mtype,msg.src,adminr)
            #         # bot.SendMsgList(msgType,rq[0],adminr)
            #         #AdminStuff(contents,msgType,rq[0])
            # #响应消息
            # if not bot.IsMe(msg.realSrc): #如果不是自己发的
            #     msg.content,atMe=bot.ClearAtMe(msg.content)
            #     if atMe:
            #         response=True
            #         responseMsg=bot.mc.GetAtResponse(msg.content)
            #     result=bot.mc.GetResponse(msg.content,msg.srcList)
            #     bot.SendStrList(msg.mtype,msg.src,result)
            # #回复（如有需要）
            # if response:
            #     resj={}
            #     resj["reply"]=responseMsg
            #     if msg.mtype=="group" or msg.mtype=="discuss":
            #         resj["at_sender"]=atSender
            #     return json.dumps(resj)
        # #提醒
        # elif postType=="notice":
        #     pass
        # #请求
        # elif postType=="request":
        #     pass
    else:
        pass
    return {}


if __name__ =='__main__':
    # app.run(host='0.0.0.0',port=8080,debug=True)
    import uvicorn
    uvicorn.run(app,host='0.0.0.0',port=8000)
