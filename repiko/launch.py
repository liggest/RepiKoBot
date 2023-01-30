
from repiko.core.bot import Bot
from repiko.core.constant import ConnectionMethod
from repiko.core.log import logger

app=None
bot=Bot()
if bot.METHOD==ConnectionMethod.HTTP:
    from repiko.core.server import getApp
    app=getApp(bot)
    def run():
        import uvicorn
        import sys
        ctx=uvicorn.main.make_context(None,["bot:app",*sys.argv[1:]])
        uvicorn.run(**ctx.params)


elif bot.METHOD in (ConnectionMethod.WS,ConnectionMethod.Combined):
    from repiko.core.websocket import main
    import uvicorn
    import sys
    from uvicorn.main import click
    def _run():
        main(bot)
    run=_run # 默认 run
    try:
        ctx=uvicorn.main.make_context(None,["bot:app",*sys.argv[1:]]) # 借用 uvicorn 内部的逻辑解析指令选项
    except click.exceptions.ClickException: # 于是 uvicorn 内部调用的库抛出了更内部的错误 
        ctx=click.Context(uvicorn.main) # 迫不得已手动创建内部库的内部对象（

    if ctx.params.get("reload"):
        def run(): # 新 run
            import watchfiles # uvicorn 用的重载库
            from pathlib import Path
            paths=ctx.params.get("reload_dirs") or [Path("repiko")]
            watchfiles.run_process(*paths,target=_run)

    del click
    del uvicorn
    del sys
            

        
        
