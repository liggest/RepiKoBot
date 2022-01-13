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
