#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask,request
from werkzeug.serving import is_running_from_reloader
import random
import json

app = Flask(__name__)
bot=None
if not is_running_from_reloader():
    import repiko.core.bot as bot_core
    bot=bot_core.Bot()

@app.route('/',methods=['POST'])
def MessageReceiver():
    rd=request.get_data()
    if bot.Verification(request,rd):
        rj=json.loads(rd)#request.get_data(as_text=True)
        #DEBUG
        if bot.DebugMode:
            print(rj)
        postType=rj["post_type"]
        #回复相关
        if postType=="message":
            response=False
            responseMsg=""
            atSender=True
            #基础信息
            msgType=rj["message_type"]
            contents=rj["message"]
            msgID=rj["message_id"]
            #TODO 更灵活的得到回复QQ
            rq=bot.GetReceiveQQ(rj,msgType)
            #复读 2%几率复读1次 2‰几率复读3次
            temp=random.randint(1,1000)
            if temp>=500 and temp<520:
                bot.SendMessage(msgType,rq[0],contents)
            elif temp==1 or temp==1000:
                bot.SendMsgList(msgType,rq[0],[contents]*3)
            #管理
            if rq[-1] in bot.AdminQQ:
                if contents.startswith("-"):
                    adminr=bot.ac.GetAdminResponse(contents)
                    bot.SendMsgList(msgType,rq[0],adminr)
                    #AdminStuff(contents,msgType,rq[0])
            #响应消息
            if not bot.IsMe(rq[-1]): #如果不是自己发的
                contents,atMe=bot.ClearAtMe(contents)
                if atMe:
                    response=True
                    responseMsg=bot.mc.GetAtResponse(contents)
                result=bot.mc.GetResponse(contents,rq)
                bot.SendMsgList(msgType,rq[0],result)
            #回复（如有需要）
            if response:
                resj={}
                resj["reply"]=responseMsg
                if msgType=="group" or msgType=="discuss":
                    resj["at_sender"]=atSender
                return json.dumps(resj)
        #提醒
        elif postType=="notice":
            pass
        #请求
        elif postType=="request":
            pass
    else:
        pass
    return ""


if __name__ =='__main__':
    app.run(host='0.0.0.0',port=8080,debug=True)
