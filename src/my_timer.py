import asyncio
import random

class MyTimer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = None

    def start(self):
        self.cancel()
        self._task = asyncio.ensure_future(self._job())
        
    async def _job(self):
        await asyncio.sleep(self._timeout + random.random())
        await self._callback()
        
    def cancel(self):
        if self._task is not None:
            self._task.cancel()
            self._task = None
        