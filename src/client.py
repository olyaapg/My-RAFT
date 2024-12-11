import sys
import time
import httpx
import asyncio

from lock import LockEntry, LockFromClient
from state_machine import Entry


def is_locked(lock: LockEntry):
    return (lock.value != "") and (lock.end_of_lock > time.time())

def is_mine(lock: LockEntry, name: str):
    return is_locked(lock) and (lock.value == name)


async def main():
    name = args[0]
    key = "key"
    get_url = "http://localhost:5000/get/" + key
    cas_url = "http://localhost:5000/cas"

    async with httpx.AsyncClient() as client:
        response = await client.get(get_url)
        print(f"First GET response:    {response.json()}, {response.status_code}")
        if response.status_code != 200:
            data = Entry(key=key, value=LockFromClient(next_value=name, current_value="", end_of_lock=time.time() + 15, version=0))
            print(f"Send POST for lock with    {data}")
            await client.post(cas_url, json=data.model_dump())
        else:
            found_entry = LockEntry(**response.json())
            print(f"For '{key}' there is an entry    {found_entry}")
            while is_locked(found_entry):
                print("Try to lock...")
                await asyncio.sleep(2)
                response = await client.get(get_url)
                found_entry = LockEntry(**response.json())
            data = Entry(key=key, value=LockFromClient(next_value=name, current_value=found_entry.value, end_of_lock=time.time() + 15, version=found_entry.version))
            print(f"Unlocked! Try to lock with    {data}")
            await client.post(cas_url, json=data.model_dump())
        for _ in range(1, 5):
            await asyncio.sleep(4)
            response = await client.get(get_url)
            print(f"Check '{key}' for locked: {is_mine(LockEntry(**response.json()), name)}")
            


if __name__ == "__main__":
    args = sys.argv[1:]
    asyncio.run(main())
