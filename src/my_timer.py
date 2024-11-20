import asyncio
import random


class MyTimer:

    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = None
        self.mutex = asyncio.Lock()

    async def start(self):

        await self.cancel()
        print(f"restart {self._timeout}")
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        # await self.mutex.acquire()
        print("END1 TIMER")
        await asyncio.sleep(self._timeout + random.random())
        await self._callback()
        print("END2 TIMER")
        # self.mutex.release()

    async def cancel(self):
        # await self.mutex.acquire()
        if self._task is not None:
            print(f"cancel {self._timeout}")
            # await asyncio.wait(self._task)
            self._task.cancel()
            self._task = None
        # self.mutex.release()
