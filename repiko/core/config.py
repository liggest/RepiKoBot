from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from repiko.config import Config, Pattern
from repiko.core.constant import ConnectionMethod

if TYPE_CHECKING:
    config:Config  # 基础配置
    pluginConfig:Config  # 插件配置

_configName="config.toml"
_pluginConfigName="plugin.toml"

class BotConfig:
    """  配置  """
    
    class Admin:
        adminQQ:Annotated[list[int],"管理者 QQ"] = [10086]
    
    admin:Admin  # admin = { "adminQQ":[10086] }

    class Bot:
        """  bot 相关  """
        name = "RepiKo"
        myQQ = 1233456
    
    bot:Bot  # bot = { "name":"RepiKo", "myQQ":1233456 }

    class Connection:
        """  默认优先 ws，ws 无内容则使用 http  """
        class WS:
            url:Annotated[str|None,"正向 WS 监听地址的 url"] = "ws://127.0.0.1:8080/"
        class Http:
            url:Annotated[str|None,"HTTP 监听地址的 url（不是 post 的 url）"] = "http://127.0.0.1:5700/"
            secret:Annotated[str|None,"post 密钥"]
        
        http:Http|None
        ws:WS|None
    
    connection:Connection
    # connection = { 
    #     "http":{ "url":None, "secret":None },
    #     "ws":  { "url":None }
    # }

class PluginConfig(Pattern):
    """  各种插件的配置  """

# PluginConfig=Config.Unit("PluginConfig", dict, "各种插件的配置")
PluginGroup=PluginConfig

# cfg=None

# @Config.considerClass
# class Admin:
#     adminQQ:Annotated[list[int],"管理者 QQ"] = [10086]

# @Config.considerClass
# class Bot:
#     """  bot 相关  """
#     name = "RepiKo"
#     myQQ = 1233456

# @Config.considerClass
# class Connection:
#     """  默认优先 ws，ws 无内容则使用 http  """
#     class WS:
#         url:Annotated[str|None,"正向 WS 监听地址的 url"] = "ws://127.0.0.1:8080/"
#     class Http:
#         url:Annotated[str|None,"HTTP 监听地址的 url（不是 post 的 url）"] = "http://127.0.0.1:5700/"
#         secret:Annotated[str|None,"post 密钥"]
    
#     http:Http|None
#     ws:WS|None

# BotCFG = Config.Unit("BotCFG",dict,doc="配置")

# BotCFG.addDefault("admin",anno=Admin)
# BotCFG.addDefault("bot",anno=Bot)
# BotCFG.addDefault("connection",anno=Connection)

class ConnectionInfo:
    
    def __init__(self) -> None:
        self.URL:str=None
        self.POSTURL:str=None
        self.SECRET=""
        self.METHOD=ConnectionMethod.Unknown

    @staticmethod
    def get(config:BotConfig.Connection | dict, self:ConnectionInfo=None):
        """  从 config 中为 self 添加连接信息  """
        self = self or ConnectionInfo()
        httpConn = config.http
        wsConn = config.ws
        if httpConn and (httpURL:=httpConn.url):
        # if httpConn and (httpURL:=httpConn.url):
            self.URL=httpURL
            self.POSTURL=httpURL
            self.SECRET=str.encode(httpConn.secret or "")
            # self.SECRET=str.encode(httpConn.secret)
            self.METHOD=ConnectionMethod.HTTP
        if wsConn and (wsURL:=wsConn.url): # ws 覆盖 http
        # if wsConn and (wsURL:=wsConn.url): # ws 覆盖 http
            self.URL=wsURL
            self.METHOD=ConnectionMethod.WS
        if not self.URL: # 未找到 self.URL
            raise ValueError(f"未找到连接信息！请在 {_configName} 中修改配置")
        
        if self.METHOD==ConnectionMethod.WS and self.POSTURL:
            self.METHOD=ConnectionMethod.Combined
        return self


def _getConfig():
    global config, BotConfig
    config = Config(_configName)
    BotConfig = config.defaults(BotConfig)
    return config

def _getPluginConfig():
    global pluginConfig
    pluginConfig = Config(_pluginConfigName).withDefaults(PluginConfig)
    return pluginConfig

def __getattr__(name):  # 延迟加载 config 和 pluginConfig
    # logger.debug(f"[{name}]")
    if name=="config":
        return _getConfig()
    elif name=="pluginConfig":
        return _getPluginConfig()
    raise AttributeError
