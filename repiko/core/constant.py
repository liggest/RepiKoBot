from enum import Enum

class ConnectionMethod(str,Enum):
    """  通信方法  """
    Unknown="unknown"
    """ 一般不用这个 """
    HTTP="http"
    """ http post """
    WS="ws"
    """ 正向 WebSocket """
    Combined="combined"
    """ 正向 WebSocket（可用 http 调用 api） """

class PostType(str,Enum):
    """ 事件类型 """
    Unknown="unknown"
    """ 一般不用这个 """
    Message="message"
    """ 消息事件 """
    Notice="notice"
    """ 通知事件 """
    Request="request"
    """ 请求事件 """
    Meta="meta_event"
    """ 元事件 """

class MessageType(str,Enum):
    """ 消息事件类型 """
    Unknown="unknown"
    """ 一般不用这个 """
    Private="private"
    """ 私聊消息 """
    Group="group"
    """ 群聊消息 """

class RequestType(str,Enum):
    """ 请求事件类型 """
    Unknown="unknown"
    """ 一般不用这个 """
    Friend="friend"
    """ 加好友请求 """
    Group="group"
    """ 加群请求/加群邀请 """

class NoticeType(str,Enum):
    """ 通知事件类型 """
    Unknown="unknown"
    """ 一般不用这个 """
    FriendAdd="friend_add"
    """ 好友添加 """
    FriendRecall="friend_recall"
    """ 好友消息撤回 """
    GroupUpload="group_upload"
    """ 群文件上传 """
    GroupAdmin="group_admin"
    """ 群管理员变动 """
    GroupDecrease="group_decrease"
    """ 群成员减少 """
    GroupIncrease="group_increase"
    """ 群成员增加 """
    GroupBan="group_ban"
    """ 群禁言 """
    GroupRecall="group_recall"
    """ 群消息撤回 """
    GroupCard="group_card"
    """ 群成员名片更新 """
    Notify="notify"
    """ 群提醒（戳一戳、红包运气王、荣誉变更）等 """
    OfflineFile="offline_file"
    """ 接收到离线文件 """
    ClientStatus="client_status"
    """ 其他客户端在线状态变更 """
    Essence="essence"
    """ 精华消息 """
    GroupMsgEmojiLike = "group_msg_emoji_like"
    """ 群聊表情回应 """

class MetaEventType(str,Enum):
    """ 请求事件类型 """
    Unknown="unknown"
    """ 一般不用这个 """
    Lifecycle="lifecycle"
    """ 生命周期 """
    HeartBeat="heartbeat"
    """ 心跳 """

class EventNames:
    """ 各种 bot 事件名 """

    Startup="bot-Startup"
    """ bot 启动 \n (bot:Bot) -> None """
    Shutdown="bot-Shutdown"
    """ bot 关闭 \n (bot:Bot) -> None """
    MsgCoreInit="msgcore-Init"
    """ msg.core 初始化 \n (core:MCore) -> None """

    @staticmethod
    def Receive(pt:PostType):
        """  收到 pt 事件 \n\n (msg:Message,bot:Bot) -> None """
        return f"receive-{pt.name}"

    AtMe="msg-AtMe"
    """ 收到 @bot 的消息 \n (msg:Message,bot:Bot) -> None """
    ReplyMe="msg-ReplyMe"
    """ 收到回复 bot 的消息 \n (msg:Message,bot:Bot) -> None """
    # PokeMe="msg-PokeMe"
    # """ 收到戳 bot 的消息 \n (msg:Message,bot:Bot) -> None """
    # WithDraw="notice-WithDraw"
    # """ 收到撤回消息 \n (nti:Notice,bot:Bot) -> None """
    MsgFilter="msg-Filter"
    """ 返回 True 时过滤当前消息 \n (msg:Message,bot:Bot) -> bool """

    @staticmethod
    def ConfigInit(path:str):
        """  从 path 加载配置时 \n\n (config: dict | list ,bot:Bot) -> None """
        return f"config-{path}-init"

    @staticmethod
    def ConfigUpdate(path:str):
        """  配置更新时 \n\n (config: dict | list ,bot:Bot) -> None """
        return f"config-{path}-update"
