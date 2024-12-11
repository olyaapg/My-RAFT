from pydantic import BaseModel

from state_machine import Entry


class LockEntry(BaseModel):
    lock_name: str
    lock_owner: str
    lock_ttl: int   # в секундах
    lock_version: int


class SetData(BaseModel):
    lock_owner: str
    lock_version: int
    entry: Entry
    

