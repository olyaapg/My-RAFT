from pydantic import BaseModel


class LockEntry(BaseModel):
    lock_name: str
    lock_owner: str
    lock_ttl: int   # в секундах
    lock_version: int
