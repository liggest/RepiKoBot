
# import requests
import httpx

class HitokotoRequester():

    str2type={
        "动画":"a","漫画":"b","游戏":"c","文学":"d","原创":"e","网络":"f","其他":"g",
        "影视":"h","诗词":"i","网易云":"j","哲学":"k"#,"抖机灵":"l"
    }
    type2str= dict(map(reversed,str2type.items()))

    encode="json"
    #charset="utf-8"
    url=r"https://v1.hitokoto.cn/"

    def __init__(self):
        self.clist=[]

    def params(self,*types):
        notfill=self.fillClist(*types)
        if notfill:
            for x in notfill:
                self.fillClist(*list(x))
        if self.clist:
            params={"c":self.clist,"encode":"json"}
        else:
            params={"encode":"json"}
        return params

    def word(self,rj):
        word=rj["hitokoto"]+"\n        ——"
        if rj["from_who"]:
            word+=" "+rj["from_who"]
        if rj["from"]:
            word+=f"「{rj['from']}」"
        return word

    def request(self,*types):
        
        #print(self.clist)
        # r = requests.get(self.url,params=self.params(*types))
        r = httpx.get(self.url,params=self.params(*types))
        rj=r.json()
        # print(rj)
        return self.word(rj)

    async def aRequest(self,*types):
        async with httpx.AsyncClient() as client:
            r=await client.get(self.url,params=self.params(*types))
            rj=r.json()
            return self.word(rj)

    def fillClist(self,*types):
        notfill=[]
        for x in types:
            t=HitokotoRequester.str2type.get(x,None)
            if t:
                self.clist.append(t)
            elif HitokotoRequester.type2str.get(x,False):
                self.clist.append(x)
            else:
                notfill.append(x)
        return notfill

if __name__ == "__main__":
    async def main():
        types=input().split()
        a=HitokotoRequester()
        print(await a.aRequest(*types))

    import asyncio
    asyncio.run(main())


