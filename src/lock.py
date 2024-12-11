from pydantic import BaseModel


class LockFromClient(BaseModel):
    next_value: str
    current_value: str
    end_of_lock: float    # в сек 
    version: int
    
class LockEntry(BaseModel):
    value: str
    end_of_lock: float 
    version: int