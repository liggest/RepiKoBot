from typing import TypedDict, Literal
from typing_extensions import NotRequired

class SenderInfo(TypedDict):
    user_id: int
    nickname: str
    sex: Literal["male", "female", "unknown"]
    age: int
    # 临时会话
    group_id: NotRequired[int]
    # 群聊
    card: NotRequired[str]
    area: NotRequired[str]
    level: NotRequired[str]
    role: NotRequired[Literal["owner", "admin", "member"]]
    title: NotRequired[str]
    """ 专属头衔 """

class GroupMemberInfo(TypedDict):
    group_id: int
    user_id: int
    nickname: str
    card: str
    sex: Literal["male", "female", "unknown"]
    age: int
    area: str
    join_time: int
    last_sent_time: int
    level: str
    role: Literal["owner", "admin", "member"]
    unfriendly: bool
    """ 是否为不良记录成员 """
    title: str
    """ 专属头衔 """
    title_expire_time: int
    card_changeable: bool
    shut_up_timestamp: int
    """ 禁言到期时间 """

class QQInfo(TypedDict):
    user_id: int
    nickname: str
    sex: Literal["male", "female", "unknown"]
    age: int
    qid: str
    """ qid ID身份卡 """
    level: str
    """ 等级 """
    login_days: int

class EssenceInfo(TypedDict):
    sender_id: int
    sender_nick: str
    sender_time: int
    operator_id: int
    operator_nick: str
    operator_time: int
    message_id: int

