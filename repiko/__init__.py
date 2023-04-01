from repiko.launch import run

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from repiko.core.server import FastAPI
    app: FastAPI

def __getattr__(name):  # 延迟加载 app
    global app
    if name == "app":
        from repiko.core.server import getApp
        app = getApp()
        return app
    raise AttributeError
