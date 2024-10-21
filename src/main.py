import asyncio
from node import Node

async def start_nodes():
    node1 = Node(5000, ["localhost:5001", "localhost:5002"])
    node2 = Node(5001, ["localhost:5000", "localhost:5002"])
    node3 = Node(5002, ["localhost:5000", "localhost:5001"])

    await asyncio.gather(
        node1.start(),
        node2.start(),
        node3.start()
    )

if __name__ == "__main__":
    asyncio.run(start_nodes())
