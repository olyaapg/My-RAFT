from fastapi import FastAPI, Header, Response
from pydantic import BaseModel
import uvicorn
import asyncio
import httpx
from contextlib import asynccontextmanager

from node_state import NodeState
from log import LogEntry
from types_of_rpc import (
    AppendEntries,
    AppendEntriesResponse,
    RequestVote,
    RequestVoteResponse,
)
from my_timer import MyTimer
from state_machine import Entry, InvalidCommandError, StateMachine, Commands


class Node:
    def __init__(self, port: int, nodes: list[str], host: str = "localhost"):
        self.host = host
        self.port = port
        self.name = host + ":" + str(port)
        self.nodes = nodes
        self.app = FastAPI(lifespan=self.lifespan)

        self.state = NodeState.FOLLOWER
        self.state_machine = StateMachine()
        self.votes_count = 0

        self.current_term = 0
        self.voted_for = None
        self.log = [
            LogEntry(command_index=Commands.GET, command_input=None, term=0, index=0)
        ]

        self.commit_index = 0
        self.last_applied = 0

        self.next_index = {}
        self.match_index = {}

        self.leader = None
        self.election_timer = MyTimer(2, self.start_election, True)
        self.leader_timer = MyTimer(0.5, self.heartbeat)

        @self.app.get("/", status_code=200)
        def hello_from_node():
            return {"message": f"Hello from Node at {self.host}:{self.port}"}

        @self.app.post("/request-vote", status_code=200)
        async def receive_request_vote(request: RequestVote):
            await self.processing_request_vote(request=request)
            return {"status": "received"}

        @self.app.post("/request-vote-response", status_code=200)
        async def receive_request_vote_response(request: RequestVoteResponse):
            await self.processing_request_vote_response(request=request)
            return {"status": "received"}

        @self.app.post("/append-entries", status_code=200)
        async def receive_append_entries(request: AppendEntries):
            await self.processing_append_entries(request=request)
            return {"status": "received"}

        @self.app.post("/append-entries-response", status_code=200)
        async def receive_append_entries_response(
            request: AppendEntriesResponse,
            node_ip: str = Header(None, alias="X-Node-Ip"),
        ):
            await self.processing_append_entries_response(node=node_ip, request=request)
            return {"status": "received"}

        @self.app.get("/get/{key}", status_code=200)
        async def receive_get_from_client(response: Response, key: str):
            # print(f"{self.state} {self.host}:{self.port} received a GET request from client: key={key}")
            try:
                result = await self.processing_get_from_client(key)
            except KeyError:
                response.status_code = 404
                return {"message": f"Key '{key}' not found"}
            return result

        @self.app.post("/set", status_code=200)
        async def receive_set_from_client(response: Response, request: Entry):
            if self.leader != self.name:
                response.status_code = 418
                if self.leader is None:
                    message = "I don't know who the leader is.🤷"
                else:
                    message = f"I'm not a leader! Send the request to 👉{self.leader}"
                return {"message": message}
            await self.processing_set_from_client(request)
            return {}
        
        @self.app.post("/cas", status_code=200)
        async def receive_cas_from_client(response: Response, request: Entry):
            if self.leader != self.name:
                response.status_code = 418
                if self.leader is None:
                    message = "I don't know who the leader is.🤷"
                else:
                    message = f"I'm not a leader! Send the request to 👉{self.leader}"
                return {"message": message}
            await asyncio.to_thread(self.processing_cas_from_client, request)
            return {}

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        print(f"Node {self.host}:{self.port} is starting...")
        self.client = httpx.AsyncClient()
        try:
            yield
        finally:
            print(f"Node {self.host}:{self.port} is shutting down...")
            await self.client.aclose()
            await self.leader_timer.cancel()
            await self.election_timer.cancel()

    async def start(self):
        await self.election_timer.start()
        config = uvicorn.Config(
            self.app, host=self.host, port=self.port, log_level="critical"
        )
        server = uvicorn.Server(config)
        await server.serve()

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
            await self.client.post(
                f"http://{receiver}/{end}",
                json=message.model_dump(),
                headers={"X-Node-Ip": self.name},
                timeout=0.05
            )
        except Exception as e:
            print(f"Failed to connect to {receiver}: {e}")

    async def send_parallel_messages(self, receivers: list[str], message: BaseModel):
        tasks = []
        for receiver in receivers:
            task = asyncio.create_task(self.send_message(receiver, message))
            tasks.append(task)
        await asyncio.gather(*tasks)

    async def processing_request_vote(self, request: RequestVote):
        # print(
        #     f"{self.state} {self.host}:{self.port} received a vote request: {request.model_dump()}"
        # )
        if request.term < self.current_term:
            vote = False
            await self.send_message(
                receiver=request.candidate_id,
                message=RequestVoteResponse(term=self.current_term, vote_granted=vote)
            )
            return
        await self.update_term(request.term)
        if (self.voted_for is not None) or (request.last_log_term < self.log[-1].term):
            vote = False
        elif (request.last_log_term == self.log[-1].term) and (
            request.last_log_index < (len(self.log) - 1)
        ):
            vote = False
        else:
            vote = True
            self.voted_for = request.candidate_id
            await self.election_timer.start()
        await self.send_message(
            receiver=request.candidate_id,
            message=RequestVoteResponse(term=self.current_term, vote_granted=vote)
        )

    async def processing_request_vote_response(self, request: RequestVoteResponse):
        # print(
        #     f"{self.state} {self.host}:{self.port} received a vote request response: {request.model_dump()}"
        # )
        await self.update_term(request.term)
        if self.state != NodeState.CANDIDATE:
            return
        if request.vote_granted == True:
            self.votes_count += 1
            if self.votes_count > ((len(self.nodes) + 1) / 2):
                await self.become_leader()

    async def processing_append_entries(self, request: AppendEntries):
        # print(
        #     f"{self.state} {self.host}:{self.port} received an append entries: {request.model_dump()}\n"
        # )
        # print(f'{request.term}, {self.current_term}')
        if request.term < self.current_term:
            await self.send_message(
                request.leader_id,
                AppendEntriesResponse(term=self.current_term, success=False),
            )
            return
        if self.state == NodeState.CANDIDATE:
            candidate = True
        else:
            candidate = False
        await self.update_term(request.term, candidate=candidate)
        self.leader = request.leader_id
        # Если индекс последнего элемента меньше индекса предыдущей записи запроса,
        # т.е. если в логе нет предыдущей записи
        if (len(self.log) - 1 < request.prev_log_index) or (
            self.log[request.prev_log_index].term != request.prev_log_term
        ):
            self.log = self.log[: request.prev_log_index]
            await self.send_message(
                request.leader_id,
                AppendEntriesResponse(term=self.current_term, success=False)
            )
            # print(f"LOG   {self.log}\n")
            await self.election_timer.start()
            return
        if len(request.entries) > 0:
            self.log.extend(request.entries)
        if request.leader_commit_index > self.commit_index:
            self.commit_index = min(request.leader_commit_index, len(self.log) - 1)
            for entry in self.log[self.last_applied + 1 : self.commit_index + 1]:
                self.state_machine.apply_command(
                    command_index=entry.command_index, command_input=entry.command_input
                )
        # print(f"LOG   {self.log}\n")
        await self.send_message(
            request.leader_id,
            AppendEntriesResponse(term=self.current_term, success=True)
        )
        await self.election_timer.start()

    async def processing_append_entries_response(
        self, node: str, request: AppendEntriesResponse
    ):
        # print(
        #     f"{self.state} {self.host}:{self.port} received an append entries response: {request.model_dump()}"
        # )
        await self.update_term(request.term)
        if self.state != NodeState.LEADER:
            return
        # Если нода ответила, что имеет запись с prev_log_index и prev_log_term,
        # и у неё ещё не все записи есть
        if request.success:
            self.match_index[node] = min(self.next_index[node], len(self.log) - 1)
            self.next_index[node] = min(self.next_index[node] + 1, len(self.log))
            if self.commit_index != len(self.log) - 1:
                self.update_commit_index()
        elif not request.success:
            self.next_index[node] -= 1
            self.match_index[node] = 0

    async def processing_set_from_client(self, data: Entry):
        # print(
        #     f"{self.state} {self.host}:{self.port} received a set request from client: {data}"
        # )
        new_entry_index = len(self.log)
        self.log.append(
            LogEntry(
                command_index=Commands.SET,
                command_input=data,
                term=self.current_term,
                index=new_entry_index
            )
        )

        async def wait_for_applying():
            while self.last_applied < new_entry_index:
                await asyncio.sleep(1)

        await wait_for_applying()

    async def processing_get_from_client(self, key: str):
        entry = Entry(key=key, value=None)
        entry.value = await asyncio.to_thread(self.state_machine.apply_command, Commands.GET, entry)
        return entry.value

    def processing_cas_from_client(self, data: Entry):
        # print(
        #     f"{self.state} {self.host}:{self.port} received a cas request from client: {data}"
        # )
        new_entry_index = len(self.log)
        self.log.append(
            LogEntry(
                command_index=Commands.CAS,
                command_input=data,
                term=self.current_term,
                index=new_entry_index
            )
        )

    async def start_election(self):
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.votes_count = 1
        self.voted_for = self.name
        self.leader = None
        # print(f"{self.name}: election is starting! Term - {self.current_term}")
        await self.send_parallel_messages(
            self.nodes,
            RequestVote(
                term=self.current_term,
                candidate_id=self.name,
                last_log_index=len(self.log) - 1,
                last_log_term=self.log[-1].term
            ),
        )
        await self.election_timer.start()

    async def become_leader(self):
        # print(f"{self.name}: I'm a leader!")
        self.state = NodeState.LEADER
        await self.election_timer.cancel()
        self.leader = self.name
        for node in self.nodes:
            self.next_index[node] = len(self.log)
            self.match_index[node] = 0
        await self.heartbeat()

    async def heartbeat(self):
        print("HB")
        tasks = []
        for node in self.nodes:
            prev_log_index = self.next_index[node] - 1
            entries = []
            if len(self.log) > self.next_index[node]:
                entries = [self.log[self.next_index[node]]]
            tasks.append(
                self.send_message(
                    node,
                    AppendEntries(
                        term=self.current_term,
                        leader_id=self.name,
                        prev_log_index=prev_log_index,
                        prev_log_term=self.log[prev_log_index].term,
                        entries=entries,
                        leader_commit_index=self.commit_index
                    ),
                )
            )
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as ex:
            print("heartbeat gather ex", ex)
        await self.leader_timer.start()

    async def update_term(self, term: int, candidate=False):
        if term > self.current_term or candidate:
            self.current_term = term
            self.state = NodeState.FOLLOWER
            # print("When updating the term, I became a FOLLOWER")
            await self.leader_timer.cancel()
            self.voted_for = None
            self.votes_count = 0
            await self.election_timer.start()

    # If there exists an N such that N > commitIndex, a majority
    # of matchIndex[i] ≥ N, and log[N].term == currentTerm:
    # set commitIndex = N
    def update_commit_index(self):
        for N in range(self.commit_index + 1, len(self.log)):
            count = sum(1 for match in self.match_index.values() if match >= N)
            if count + 1 > ((len(self.nodes) + 1) / 2):
                if self.log[N].term == self.current_term:
                    self.commit_index = N
            else:
                break
        for i in range(self.last_applied + 1, self.commit_index + 1):
            try:
                self.state_machine.apply_command(
                    self.log[i].command_index, self.log[i].command_input
                )
            except InvalidCommandError as e:
                print(f"Сообщение об ошибке: {e}")
            finally:
                self.last_applied += 1
