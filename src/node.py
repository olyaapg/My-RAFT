import threading
import asyncio
import pickle
from node_state import NodeState
from types_of_rpc import RequestVote, RequestVoteResponse
from my_timer import MyTimer

class Node:
    def __init__(self, host: str, port: int, list_ip: list[str]):
        self.host = host
        self.port = port
        self.name = 'http://' + host + ':' + str(port)
        self.app = Flask(self.name) # Основной класс приложения Flask. Он управляет маршрутизацией, настройками и запускает веб-сервер.
        self.start()
        self.nodes_sessions = {}
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.votes_count = 0
        self.commit_index = 0
        self.last_applied = 0
        self.last_log_term = 0
        for key in ['http://' + ip for ip in list_ip]:
            self.nodes_sessions[key] = None
        self.next_index = {}
        self.match_index = {}
        self.refresh_next_match_index()
        self.election_timer = MyTimer(self.start_election)
        self.election_timer.start()
        
        # Обработчик для входящих сообщений
        # TODO: доделать
        @self.app.route('/', methods=['POST'])
        def receive_message():
            print("HERERERERER")
            asyncio.get_running_loop()
            print("HERE IT IS")
            data = pickle.loads(request.get_data())
            print(f"{self.name} получил сообщение: {data}")
            if isinstance(data, RequestVote): # если пришел запрос RequestVote
                self.respond_to_RequestVote(data)
            if isinstance(data, RequestVoteResponse) & self.state == NodeState.CANDIDATE:
                self.receive_RequestVoteResponse(data)
            return jsonify({"status": "received"}), 200 # response (jsonify): Объект ответа, который возвращается клиенту.

    def start(self):
        # Запускаем Flask сервер в отдельном потоке
        thread = threading.Thread(target=self.run_server)
        thread.daemon = True  # Сделаем поток демоном, чтобы он завершился при остановке программы
        thread.start()

    def run_server(self):
        print(f"{self.name} запущен на порту {self.port}")
        self.app.run(port=self.port, host='0.0.0.0')

    async def send_message(self, receiver_url: str, message):
        if self.nodes_sessions[receiver_url] is None:
            self.nodes_sessions[receiver_url] = aiohttp.ClientSession()
        session = self.nodes_sessions[receiver_url] 
        headers = {"Content-Type": "application/octet-stream"}
        try:
            async with session.post(receiver_url, data=pickle.dumps(message), headers=headers) as response:
                if response.status == 200:
                    print(f"{self.name} успешно отправил: {message}")
                else:
                    print(f"Ошибка при отправке сообщения: {response.status}")
        except Exception as e:
            print(f"Ошибка подключения: {e}")
                
    async def send_parallel_messages(self, receivers: list[str], message):
        tasks = []
        for receiver in receivers:
            task = asyncio.create_task(self.send_message(receiver, message))
            tasks.append(task)
        await asyncio.gather(*tasks)
        
    # Нужно вызвать в конце!
    async def stop(self):
        for session in self.nodes_sessions.values():
            if session is not None:
                await session.close()
        self.election_timer.cancel()
                
    # Вызвать после становления лидером!
    def refresh_next_match_index(self):
        for key in self.nodes_sessions.keys():
            self.next_index[key] = len(self.log)
            self.match_index[key] = 0
            
    # TODO: убрать хардкод в конце функции!
    def start_election(self):
        print(f"{self.name}: election is starting!")
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.votes_count = 1
        self.voted_for = self.name
        self.election_timer.start()
        asyncio.create_task(self.send_parallel_messages(self.nodes_sessions.keys(), RequestVote(self.current_term, self.name, len(self.log) - 1, 0)))
    
    def respond_to_RequestVote(self, request: RequestVote):
        if (self.voted_for is not None) | (request.term < self.current_term) | (request.last_log_term < self.last_log_term):
            vote = False
        elif (request.last_log_term == self.last_log_term) & (request.last_log_index < (len(self.log) - 1)):
            vote = False
        else:
            vote = True
            self.election_timer.start() # сбрасываем таймер
            self.current_term = request.term
            self.voted_for = request.candidate_id
        data = RequestVoteResponse(self.current_term, vote_granted=vote)
        asyncio.create_task(self.send_message(request.candidate_id, data))
        # print("HERERERERERER")
        # asyncio.get_running_loop()
        # print("asyncio.get_running_loop()")
    
    def receive_RequestVoteResponse(self, response: RequestVoteResponse):
        if response.vote_granted == True:
            self.votes_count += 1
            if self.votes_count > (len(self.nodes_sessions) / 2):
                print(f'I\'m {self.name} a new leader!')
