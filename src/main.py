import asyncio
import sys
from node import Node

#py src\main.py 5000 localhost:5001 localhost:5002 localhost:5003
async def main():
    node = Node(int(args[0]), args[1:])
    await node.start()

if __name__ == "__main__":
    args = sys.argv[1:]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()