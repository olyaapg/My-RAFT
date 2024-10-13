import asyncio

class MyTimer:
    def __init__(self, interval, function):
        self.interval = interval
        self.function = function
        self.task = None

    async def _run(self):
        await asyncio.sleep(self.interval)
        self.function()

    def start(self):
        self.cancel()
        self.task = asyncio.create_task(self._run())

    def cancel(self):
        if self.task is not None:
            self.task.cancel()
            self.task = None

