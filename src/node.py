from email import message
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import asyncio
import httpx
from contextlib import asynccontextmanager

from node_state import NodeState
from types_of_rpc import RequestVote, RequestVoteResponse
from my_timer import MyTimer



class Node:
    def __init__(self, port: int, nodes: list[str], host: str = "localhost"):
        self.host = host
        self.port = port
        self.name = 'http://' + host + ':' + str(port)
        self.nodes = nodes
        self.app = FastAPI(lifespan=self.lifespan)
        
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.votes_count = 0
        self.commit_index = 0
        self.last_applied = 0
        self.last_log_term = 0
        self.next_index = {}
        self.match_index = {}
        # self.refresh_next_match_index()
        # self.election_timer = MyTimer(self.start_election)
        # self.election_timer.start()
               
        @self.app.get("/")
        async def hello_from_node():
            return {"message": f"Hello from Node at {self.host}:{self.port}"}

        @self.app.get("/request-vote")
        async def send_request_vote():
            await self.send_parallel_messages(self.nodes, RequestVote(term=1, candidate_id=self.name, last_log_index=0, last_log_term=0))
            return {"message": "отправил"}
        
        @self.app.post("/request-vote")
        async def receive_request_vote(vote: RequestVote):
            print(f"Node {self.host}:{self.port} received a vote request: {vote}")
            return {"message": f"Node {self.host}:{self.port} received a vote request", "vote_data": vote.model_dump()}

        # @self.app.post("/request-vote", response_model=RequestVoteResponse)
        # async def request_vote(request: RequestVote):
        #     print(f"Получен запрос голосования от {request.candidate_id} на ноде {app.state.node.name}")
        #     # Пример обработки запроса голосования
        #     vote_granted = True  # Здесь ваша логика голосования
        #     return RequestVoteResponse(term=request.term, vote_granted=vote_granted)

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
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
        
    async def send_message(self, receiver: str, message: BaseModel):
        try:
            response = await self.client.post(f"http://{receiver}/request-vote", json=message.model_dump())
            print(f"Response from {receiver}: {response.json()}")
        except Exception as e:
            print(f"Failed to connect to {receiver}: {e}")
                    
    async def send_parallel_messages(self, receivers: list[str], message: BaseModel):
        tasks = []
        for receiver in receivers:
            task = asyncio.create_task(self.send_message(receiver, message))
            tasks.append(task)
        await asyncio.gather(*tasks)
