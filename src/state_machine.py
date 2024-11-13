from enum import Enum


class Commands(Enum):
    GET = 0
    SET = 1


class StateMachine:
    def __init__(self):
        self.hash_map = {}

    def get(self, key):
        return self.hash_map[key]

    def set(self, key, value):
        self.hash_map[key] = value
        return self.hash_map[key]

    def apply_command(self, command_index, command_input):
        if command_index == Commands.GET.value:
            return self.get(command_input["key"])
        elif command_index == Commands.SET.value:
            return self.set(command_input["key"], command_input["value"])
        else:
            print("Error: Unsupported command")
            return None
