
from repiko.core.bot import Bot
from repiko.core.constant import ConnectionMethod
from repiko.core.log import logger

from repiko.core.config import config, ConnectionInfo, BotConfig

app=None

if config.data is None:
    config.init()

data:BotConfig=config.data
conn=ConnectionInfo.get(data.connection)

# bot=Bot()
if conn.METHOD==ConnectionMethod.HTTP:
    from repiko.core.server import getApp
    # app=getApp(Bot())
    app=getApp()

    def run():
        # TODO
        # import uvicorn
        import sys
        from subprocess import Popen
        import signal
        sigMap={signal.SIGTERM:"SIGTERM", signal.SIGINT:"SIGINT"}
        if "--port" not in sys.argv:
            sys.argv.append("--port")
            sys.argv.append("5701")
        pro=Popen(("pdm","run","uvicorn","bot:app",*sys.argv[1:]))

        def callback(sig:int,frame=None):
            logger.debug(f"检测到 {sigMap[sig]}")
            pro.send_signal(signal.SIGTERM)

        for sig in sigMap:
            signal.signal(sig,callback)
        
        pro.wait()
        # ctx=uvicorn.main.make_context(None,["bot:app",*sys.argv[1:]])
        # uvicorn.run(**ctx.params)


elif conn.METHOD in (ConnectionMethod.WS, ConnectionMethod.Combined):
    from repiko.core.websocket import main
    # import uvicorn
    import sys
    # from uvicorn.main import click

    def _run():
        main(Bot())
    run=_run # 默认 run
    
    # try:
    #     ctx=uvicorn.main.make_context(None,["bot:app",*sys.argv[1:]]) # 借用 uvicorn 内部的逻辑解析指令选项
    # except click.exceptions.ClickException: # 于是 uvicorn 内部调用的库抛出了更内部的错误 
    #     ctx=click.Context(uvicorn.main) # 迫不得已手动创建内部库的内部对象（

    # if ctx.params.get("reload"):
    if "--reload" in sys.argv:
        
        def run(): # 新 run
            import watchfiles # uvicorn 用的重载库
            from pathlib import Path
            # paths=ctx.params.get("reload_dirs") or [Path("repiko")]
            paths=[ Path("repiko") ]
            watchfiles.run_process(*paths,target=_run)

    # del click
    # del uvicorn
    del sys
    

        
        
