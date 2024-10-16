from enum import Enum

class NodeState(Enum):
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2
