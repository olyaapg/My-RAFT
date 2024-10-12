class RequestVote:
    def __init__(self, term: int, candidate_id: str, last_log_index: int, last_log_term: int):
        self.term = term
        self.candidate_id = candidate_id
        self.last_log_index = last_log_index
        self.last_log_term = last_log_term
    
    def __str__(self):
        return "RequestVote, term " + str(self.term)
    
    
class RequestVoteResponse:
    def __init__(self, term: int, vote_granted: bool):
        self.term = term
        self.vote_granted = vote_granted
    
    def __str__(self):
        return "RequestVoteResponse, term " + str(self.term) + ", " + self.vote_granted
    
    
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