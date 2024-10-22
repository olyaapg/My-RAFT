import asyncio
from node import Node

if __name__ == "__main__":
    node = Node(5002, ["localhost:5000", "localhost:5001"])
    asyncio.run(node.start())
