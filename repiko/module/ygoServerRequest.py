#coding:utf-8
import requests
# import json

class ygoServerRequester():
    def __init__(self):
        self.url=r"http://47.94.214.137:8888/"
        self.header={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',"Content-Type": "application/json"}
    
    def request(self,exp):
        msg={"message":exp}
        r=requests.post(self.url, json=msg,headers=self.header)
        print(r.text)
        try:
            rj=r.json()
            return rj["message"]
        except:
            return "虽然不知道问题在哪，但是出错了！"
        