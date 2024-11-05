import asyncio
from node import Node

async def main():
    node = Node(5002, ["localhost:5001", "localhost:5000"])
    await node.start()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(main())
finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()