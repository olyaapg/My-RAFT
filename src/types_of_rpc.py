from pydantic import BaseModel

class RequestVote(BaseModel):
    term: int
    candidate_id: str
    last_log_index: int
    last_log_term: int
    
class RequestVoteResponse(BaseModel):
    term: int
    vote_granted: bool
    
class AppendEntries(BaseModel):
    term: int 
    leader_id: str
    prev_log_index: int
    prev_log_term: int
    entries: list
    leader_commit_index: int

class AppendEntriesResponse(BaseModel):
    term: int
    success: bool
