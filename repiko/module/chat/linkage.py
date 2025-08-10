from __future__ import annotations

import heapq
from itertools import chain
from typing import Iterator
from dataclasses import dataclass

from chat.model import Session, Dialogue

@dataclass
class DialogueByCreateTime:
    dialogue: Dialogue | None
    remaining: Iterator[Dialogue]

    def __lt__(self, other: DialogueByCreateTime):
        return self.dialogue.create_time < other.dialogue.create_time

    def __le__(self, other: DialogueByCreateTime):
        return self.dialogue.create_time <= other.dialogue.create_time
    
    def __gt__(self, other: DialogueByCreateTime):
        return self.dialogue.create_time > other.dialogue.create_time
    
    def __ge__(self, other: DialogueByCreateTime):
        return self.dialogue.create_time >= other.dialogue.create_time
    
    # def __eq__(self, other: DialogueByCreateTime):
    #     return self.dialogue.create_time == other.dialogue.create_time

    def iter_next(self):
        self.dialogue = next(self.remaining, None)
        return self.dialogue

class LinkedSession(Session):
    def __init__(self, main: Session, *others: Session):
        self.main_session = main
        self.sessions = {session.id: session for session in others}

    @property
    def id(self):
        return self.main_session.id
    
    @property
    def model_name(self):
        return self.main_session.model_name

    @property
    def llm(self):
        return self.main_session.llm

    @property
    def mcp(self):
        return self.main_session.mcp

    @property
    def expire_time(self):
        return self.main_session.expire_time
    
    @property
    def _raw_messages(self):
        return self.main_session._raw_messages
    
    def dialogues_gen(self):
        dialogue_heap: list[DialogueByCreateTime] = []
        for session in chain((self.main_session,), self.sessions.values()):
            if not session._raw_messages:
                continue
            remaining = iter(session._raw_messages)
            item = DialogueByCreateTime(None, remaining)
            if item.iter_next() is not None:
                heapq.heappush(dialogue_heap, item)

        while dialogue_heap:
            item = heapq.heappop(dialogue_heap)
            assert item.dialogue is not None
            yield item.dialogue
            if item.iter_next() is not None:
                heapq.heappush(dialogue_heap, item)

    def messages_gen(self):
        for dialogue in self.dialogues_gen():
            yield from dialogue.messages_gen()

    def rotate(self, max_tokens: int):
        rotate_session = self.main_session
        for session in self.sessions.values():
            if session.is_expired and session.create_time <= rotate_session.create_time:
                rotate_session = session
        rotate_session.rotate(max_tokens)

    def link(self, session: Session):
        if isinstance(session, LinkedSession):
            session = session.main_session

        self.sessions[session.id] = session
    
    def unlink(self, session_id):
        return self.sessions.pop(session_id, None)

