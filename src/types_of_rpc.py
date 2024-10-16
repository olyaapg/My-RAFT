from pydantic import BaseModel

class RequestVote(BaseModel):
    term: int
    candidate_id: str
    last_log_index: int
    last_log_term: int
    
    def __str__(self):
        return "RequestVote from " + self.candidate_id + ", term " + str(self.term)
    
    
class RequestVoteResponse(BaseModel):
    term: int
    vote_granted: bool
    
    def __str__(self):
        return "RequestVoteResponse, term " + str(self.term) + ", " + str(self.vote_granted)
    
    
class AppendEntries:
    def __init__(self, term: int, leader_id: str, prev_log_index: int, prev_log_term: int, entries: list, leader_commit_index: int):
        self.term = term
        self.leader_id = leader_id
        self.prev_log_index = prev_log_index
        self.prev_log_term = prev_log_term
        self.entries = entries
        self.leader_commit_index = leader_commit_index
    
    def __str__(self):
        return ("AppendEntriesRequest, term " +
                str(self.term) + ", log state: [" +
                str(self.prev_log_index) + ", " +
                str(self.prev_log_term) + ", " +
                str(self.leader_commit_index) + "]" +
                ": " + str(self.entries))