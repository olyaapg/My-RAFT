from enum import Enum
from typing import Any
from pydantic import BaseModel


class Entry(BaseModel):
    key: str
    value: Any


class Commands(int, Enum):
    GET = 0
    SET = 1


class InvalidCommandError(Exception):
    """Ошибка для случая, когда команда не распознана."""

    pass


class StateMachine:
    def __init__(self):
        self.hash_map = {}

    def get(self, key):
        return self.hash_map[key]

    def set(self, key, value):
        self.hash_map[key] = value
        return self.hash_map[key]

    def apply_command(self, command_index: Commands, command_input: Entry):
        if command_index == Commands.GET:
            return self.get(command_input.key)
        elif command_index == Commands.SET:
            return self.set(command_input.key, command_input.value)
        else:
            raise InvalidCommandError("Вызвана несуществующая команда")
