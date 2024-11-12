from typing import Any
from pydantic import BaseModel
from state_machine import Commands


class LogEntry(BaseModel):
    command_index: Commands
    command_input: Any
    term: int
    index: int
