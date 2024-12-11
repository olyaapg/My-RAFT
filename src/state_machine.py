from enum import Enum
from typing import Any
from pydantic import BaseModel

from lock import LockEntry, LockFromClient


class Entry(BaseModel):
    key: str
    value: Any


class Commands(int, Enum):
    GET = 0
    SET = 1
    CAS = 2


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
    
    def compare_and_swap(self, key: str, data: LockFromClient):
        try:
            found: LockEntry = self.hash_map[key]
            if (found.value == data.current_value and found.version == data.version):
                found.version += 1
                self.hash_map[key] = LockEntry(value=data.next_value, end_of_lock=data.end_of_lock, version=found.version)
                return True, None
            return False, None
        except KeyError as e:
            if len(data.current_value) == 0:
                self.hash_map[key] = LockEntry(value=data.next_value, end_of_lock=data.end_of_lock, version=1)
                return True, None
            return False, f"For key '{key}' waited value '{data.current_value}' but was an empty value."

    def apply_command(self, command_index: Commands, command_input: Entry):
        if command_index == Commands.GET:
            return self.get(command_input.key)
        elif command_index == Commands.SET:
            return self.set(command_input.key, command_input.value)
        elif command_index == Commands.CAS:
            return self.compare_and_swap(command_input.key, LockFromClient(**command_input.value))
        else:
            raise InvalidCommandError("Вызвана несуществующая команда")
