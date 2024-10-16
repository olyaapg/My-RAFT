import uvicorn
import argparse
from node import Node
from fastapi import FastAPI
from types_of_rpc import RequestVote, RequestVoteResponse
import httpx


app = FastAPI()


# Информация о текущей ноде
node_id = "localhost:5000"  
peers = ["localhost:5001", "localhost:5002"]

@app.get("/")
async def root():
    return {"message": RequestVote(term=1, candidate_id='1', last_log_index=0, last_log_term=0)}

@app.post("/request-vote", response_model=RequestVoteResponse)
async def request_vote(request: RequestVote):
    print(f"Получен запрос голосования от {request.candidate_id} на ноде {node_id}")
    # Пример обработки запроса голосования
    vote_granted = True  # Здесь ваша логика голосования
    return RequestVoteResponse(term=request.term, vote_granted=vote_granted)

# @app.post("/send-message")
# async def send_message():
#     async with httpx.AsyncClient() as client:
#         for peer in peers:
#             try:
#                 response = await client.post(f"http://{peer}/request-vote", json={
#                     "term": 1,
#                     "candidate_id": node_id,
#                     "last_log_index": 0,
#                     "last_log_term": 0
#                 })
#                 data = response.json()
#                 print(f"Ответ от {peer}: {data}")
#             except Exception as e:
#                 print(f"Ошибка при подключении к ноде {peer}: {e}")

#     return {"status": "Сообщения отправлены"}

def start_node(host: str, port: int, peers: list[str]):
    app.state.node_id = f"{host}:{port}"
    app.state.peers = peers
    uvicorn.run(app, host=host, port=port)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Запуск P2P ноды Raft")
    parser.add_argument('--host', type=str, default="127.0.0.1", help="Хост для запуска ноды")
    parser.add_argument('--port', type=int, required=True, help="Порт для запуска ноды")
    parser.add_argument('--peers', nargs='+', help="Список других нод (localhost:5001 localhost:5002 и т.д.)")
    args = parser.parse_args()
    start_node(args.host, args.port, args.peers)