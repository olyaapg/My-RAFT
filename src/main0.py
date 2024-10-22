import asyncio
from node import Node

if __name__ == "__main__":
    node = Node(5000, ["localhost:5001", "localhost:5002"])
    asyncio.run(node.start())
