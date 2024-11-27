import asyncio
import random


class MyTimer:

    def __init__(self, timeout, callback, isrand = False):
        self._timeout = timeout
        self._callback = callback
        self._task = None
        self.isRand = lambda : random.random()/2 if isrand else 0

    async def start(self):
        await self.cancel()
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout + self.isRand())
        await self._callback()

    async def cancel(self):
        if self._task is not None:
            self._task.cancel()
            self._task = None
