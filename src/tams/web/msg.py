from dataclasses import dataclass
from threading import Lock
from typing import List

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Msg:
    title: str
    text: str
    type: str


@dataclass_json
@dataclass
class Msgs:
    msg: List[Msg]


class Messages:
    __messages = Msgs([])

    def __init__(self) -> None:
        self.lock = Lock()

    def add_msg(self, title: str, text: str) -> None:
        with self.lock:
            self.__messages.msg.append(Msg(title, text, "OK"))

    def add_error_msg(self, title: str, text: str) -> None:
        with self.lock:
            self.__messages.msg.append(Msg(title, text, "ERROR"))

    def get_msgs_json(self, clear: bool = False) -> str:
        with self.lock:
            json: str = self.__messages.to_json()  # type: ignore[attr-defined]
            if clear:
                self.__messages.msg.clear()
            return json
