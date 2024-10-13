from node import Node
import asyncio


async def main():    
    list_url = ['localhost:5000', 'localhost:5001', 'localhost:5002', 'localhost:5003', 'localhost:5004']
    node1 = Node('localhost', 5000, ['localhost:5001', 'localhost:5002'])

    node2 = Node('localhost', 5001, ['localhost:5000', 'localhost:5002'])
    
    node3 = Node('localhost', 5002, ['localhost:5000', 'localhost:5001'])

    await asyncio.sleep(10)

    await node1.stop()
    await node2.stop()
    await node3.stop()

# Основная программа для запуска
if __name__ == '__main__':
    asyncio.run(main())