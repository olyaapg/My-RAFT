import asyncio
import random

class MyTimer:
    def __init__(self, function):
        self.function = function
        self.task = None

    async def _run(self):
        interval = 2 + random.random() * 10
        await asyncio.sleep(interval)
        self.function()

    def start(self):
        self.cancel()
        self.task = asyncio.create_task(self._run())

    def cancel(self):
        if self.task is not None:
            self.task.cancel()
            self.task = None

