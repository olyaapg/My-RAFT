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
        if (command_index == Commands.GET):
            return self.get(command_input)
        elif (command_index == Commands.SET):
            return self.set(command_input)
        else:
            return None