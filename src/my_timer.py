import asyncio
import random

class MyTimer:
    def __init__(self, init_time, function):
        self.init_time = init_time
        self.function = function
        self.task = None

    async def _run(self):
        # interval = self.init_time + random.random() * 10
        interval = self.init_time + random.random()
        await asyncio.sleep(interval)
        self.function()

    def start(self):
        self.cancel()
        self.task = asyncio.create_task(self._run())

    def cancel(self):
        if self.task is not None:
            self.task.cancel()
            self.task = None

