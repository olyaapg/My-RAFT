from typing import Any
from pydantic import BaseModel

class LogEntry(BaseModel):
    term: int
    data: Any