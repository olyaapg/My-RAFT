from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import asyncio
import httpx
from contextlib import asynccontextmanager

from node_state import NodeState
from log import LogEntry
from types_of_rpc import AppendEntries, AppendEntriesResponse, RequestVote, RequestVoteResponse
from my_timer import MyTimer



class Node:
    def __init__(self, port: int, nodes: list[str], host: str = "localhost"):
        self.host = host
        self.port = port
        self.name = host + ':' + str(port)
        self.nodes = nodes
        self.app = FastAPI(lifespan=self.lifespan)
        
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.log = [LogEntry(term=0, data=None)]
        self.votes_count = 0
        self.commit_index = 0
        self.last_applied = 0
        self.next_index = {}
        self.match_index = {}
        # self.refresh_next_match_index()
        self.election_timer = MyTimer(6, self.start_election)
        self.leader_timer = MyTimer(2, self.heartbeat)
               
        @self.app.get("/")
        async def hello_from_node():
            return {"message": f"Hello from Node at {self.host}:{self.port}"}
        
        @self.app.post("/request-vote")
        async def receive_request_vote(request: RequestVote):
            self.processing_request_vote(request=request)
            return {"status": "received"}, 200
        
        @self.app.post("/request-vote-response")
        async def receive_request_vote_response(request: RequestVoteResponse):
            self.processing_request_vote_response(request=request)
            return {"status": "received"}, 200

        @self.app.post("/append-entries")
        async def receive_append_entries(request: AppendEntries):
            self.processing_append_entries(request=request)
            return {"status": "received"}, 200

        @self.app.post("/append-entries-response")
        async def receive_append_entries_response(request: AppendEntriesResponse):
            print(f"{self.state} {self.host}:{self.port} received an append entries response: {request.model_dump()}")
            return {"status": "received"}, 200

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        print(f"Node {self.host}:{self.port} is starting...")
        self.client = httpx.AsyncClient()
        try:
            yield
        finally:
            print(f"Node {self.host}:{self.port} is shutting down...")
            await self.client.aclose()
            # TODO: добавить выкл будильника
        
    async def start(self):
        self.election_timer.start()
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="critical")
        server = uvicorn.Server(config)
        await server.serve()
        
    def processing_request_vote(self, request: RequestVote):
        print(f"{self.state} {self.host}:{self.port} received a vote request: {request.model_dump()}")
        if (request.term < self.current_term):
            vote = False
            asyncio.create_task(self.send_message(receiver=request.candidate_id, message=RequestVoteResponse(term=self.current_term, vote_granted=vote)))
            return
        self.update_term(request.term)
        if (self.voted_for is not None) | (request.last_log_term < self.log[-1].term):
            vote = False
        elif (request.last_log_term == self.log[-1].term) & (request.last_log_index < (len(self.log) - 1)):
            vote = False
        else:
            vote = True
            self.voted_for = request.candidate_id
            self.election_timer.start()
        asyncio.create_task(self.send_message(receiver=request.candidate_id, message=RequestVoteResponse(term=self.current_term, vote_granted=vote)))
    
    def processing_request_vote_response(self, request: RequestVoteResponse):
        print(f"{self.state} {self.host}:{self.port} received a vote request response: {request.model_dump()}")
        self.update_term(request.term)
        if (self.state != NodeState.CANDIDATE):
            return
        if request.vote_granted == True:
            self.votes_count += 1
            if self.votes_count > ((len(self.nodes) + 1) / 2):
                self.become_leader()
                
    def processing_append_entries(self, request: AppendEntries):
        print(f"{self.state} {self.host}:{self.port} received an append entries: {request.model_dump()}\n")
        self.update_term(request.term)
        if (request.term < self.current_term) | (self.log[request.prev_log_index].term != request.prev_log_term):
            #asyncio.create_task(self.send_message(request.leader_id, AppendEntriesResponse(term=self.current_term, success=False)))
            return
        self.election_timer.start()
        asyncio.create_task(self.send_message(request.leader_id, AppendEntriesResponse(term=self.current_term, success=True)))
        
    async def send_message(self, receiver: str, message: BaseModel):
        if isinstance(message, RequestVote):
            end = "request-vote"
        elif isinstance(message, RequestVoteResponse):
            end = "request-vote-response"
        elif isinstance(message, AppendEntries):
            end = "append-entries"
        elif isinstance(message, AppendEntriesResponse):
            end = "append-entries-response"
        else:
            end = ""
        try:
            await self.client.post(f"http://{receiver}/{end}", json=message.model_dump())
        except Exception as e:
            print(f"Failed to connect to {receiver}: {e}")
                    
    async def send_parallel_messages(self, receivers: list[str], message: BaseModel):
        tasks = []
        for receiver in receivers:
            task = asyncio.create_task(self.send_message(receiver, message))
            tasks.append(task)
        await asyncio.gather(*tasks)

    def start_election(self):
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.votes_count = 1
        self.voted_for = self.name
        print(f"{self.name}: election is starting! Term - {self.current_term}")
        asyncio.create_task(self.send_parallel_messages(self.nodes, RequestVote(term=self.current_term, candidate_id=self.name, last_log_index=len(self.log) - 1, last_log_term=self.log[-1].term)))
        self.election_timer.start()
        
    def become_leader(self):
        print(f"{self.name}: I'm a leader!")
        self.state = NodeState.LEADER
        self.election_timer.cancel()
        self.heartbeat()
        self.leader_timer.start()
        for node in self.nodes:
            self.next_index[node] = len(self.log)
            self.match_index[node] = 0
        
    def heartbeat(self):
        asyncio.create_task(self.send_parallel_messages(self.nodes, AppendEntries(term=self.current_term, leader_id=self.name, prev_log_index=len(self.log) - 1, prev_log_term=self.log[-1].term, entries=[], leader_commit_index=self.commit_index)))
        self.leader_timer.start()
    
    def update_term(self, term: int):
        if term > self.current_term:
            self.current_term = term
            self.state = NodeState.FOLLOWER
            self.leader_timer.cancel()
            self.voted_for = None
            self.votes_count = 0
            self.election_timer.start()
            