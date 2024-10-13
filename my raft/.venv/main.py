import time
from node import Node
import asyncio
from types_of_rpc import RequestVote


async def main():
    list_url = ['localhost:5000', 'localhost:5001', 'localhost:5002', 'localhost:5003', 'localhost:5004']
    node1 = Node('localhost', 5000, ['localhost:5001', 'localhost:5002', 'localhost:5003', 'localhost:5004'])
    node1.start()

    node2 = Node('localhost', 5001, ['localhost:5000', 'localhost:5002', 'localhost:5003', 'localhost:5004'])
    node2.start()
    
    node3 = Node('localhost', 5002, ['localhost:5000', 'localhost:5001', 'localhost:5003', 'localhost:5004'])
    node3.start()
    
    node4 = Node('localhost', 5003, ['localhost:5000', 'localhost:5002', 'localhost:5001', 'localhost:5004'])
    node4.start()
    
    node5 = Node('localhost', 5004, ['localhost:5000', 'localhost:5002', 'localhost:5003', 'localhost:5001'])
    node5.start()

    time.sleep(1)  # Даем время серверу запуститься

    await node3.send_parallel_messages(['http://localhost:5000', 'http://localhost:5001', 'http://localhost:5003', 'http://localhost:5004'], RequestVote(1, node3.name, 0, 0))
    await node5.send_parallel_messages(['http://localhost:5000', 'http://localhost:5001', 'http://localhost:5003', 'http://localhost:5002'], "TEST TEST TEST")
    
    # while True:
    #     message = input(f"{node1.name}, введите сообщение (или 'exit' для выхода): ")
    #     if message.lower() == 'exit':
    #         print("Завершение работы.")
    #         break
    #     await node1.send_parallel_messages(['http://localhost:5001'], message)
        
    #     message = input(f"{node2.name}, введите сообщение (или 'exit' для выхода): ")
    #     if message.lower() == 'exit':
    #         print("Завершение работы.")
    #         break
    #     await node2.send_parallel_messages(['http://localhost:5000'], message)

    await node1.stop()
    await node2.stop()
    await node3.stop()
    await node4.stop()
    await node5.stop()

# Основная программа для запуска
if __name__ == '__main__':
    asyncio.run(main())