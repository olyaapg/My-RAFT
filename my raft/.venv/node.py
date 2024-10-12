from flask import Flask, request, jsonify
import threading
import aiohttp
import asyncio
import pickle
from node_state import NodeState

class Node:
    def __init__(self, host: str, port: int, list_ip: list[str]):
        self.host = host
        self.port = port
        self.name = host + ':' + str(port)
        self.app = Flask(self.name) # Основной класс приложения Flask. Он управляет маршрутизацией, настройками и запускает веб-сервер.
        self.nodes_sessions = {}
        self.state = NodeState.FOLLOWER
        self.currentTerm = 0
        self.votedFor = None
        self.log = []
        self.commitIndex = 0
        self.lastApplied = 0
        for key in ['http://' + ip for ip in list_ip]:
            self.nodes_sessions[key] = None
        self.next_index = {}
        self.match_index = {}
        self.refresh_next_match_index()

        # Обработчик для входящих сообщений
        @self.app.route('/', methods=['POST'])
        def receive_message():
            data = request.json # request: Объект, представляющий входящий HTTP-запрос. 
            message = data.get('message')
            sender = data.get('sender')
            print(f"{self.name} получил сообщение от {sender}: {message}")
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
        async with self.nodes_sessions[receiver_url] as session:
            payload = {"sender": self.name, "message": message}
            try:
                async with session.post(receiver_url, json=payload) as response:
                    if response.status == 200:
                        print(f"Сообщение отправлено успешно: {message}")
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
                
    # Вызвать после становления лидером!
    def refresh_next_match_index(self):
        for key in self.nodes_sessions.keys():
            self.next_index[key] = len(self.log)
            self.match_index[key] = 0