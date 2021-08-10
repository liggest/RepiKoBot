from enum import Enum

class PostType(str,Enum):
    Unknown="unknown" # 一般不用这个
    Message="message"
    Notice="notice"
    Request="request"
    Meta="meta_event"

class EventNames:

    StartUp="bot-StartUp" # (bot:Bot) -> None
    ShutDown="bot-ShutDown" # (bot:Bot) -> None
    MsgCoreInit="msgcore-Init" # (core:MCore) -> None

    @staticmethod
    def Receive(pt:PostType):
        return f"receive-{pt.name}" # (msg:Message,bot:Bot=bot) -> None