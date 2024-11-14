from typing import Any
from pydantic import BaseModel
from state_machine import Commands, Entry


class LogEntry(BaseModel):
    command_index: Commands
    command_input: Entry | None
    term: int
    index: int
