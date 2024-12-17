import sys
import time
import httpx
import asyncio

from lock import LockEntry, LockFromClient
from state_machine import Entry

# py src\client.py client1 key localhost:5001 15

def is_locked(lock: LockEntry):
    return (lock.value != "") and (lock.end_of_lock > time.time())

def is_mine(lock: LockEntry, name: str):
    return is_locked(lock) and (lock.value == name)


async def main():
    name = args[0]
    key = args[1]
    host = args[2]
    time_locking = int(args[3])
    get_url = "http://" + host + "/get/" + key
    cas_url = "http://" + host + "/cas"

    async with httpx.AsyncClient() as client:
        response = await client.get(get_url)
        print(f"First GET response:    {response.json()}, {response.status_code}")
        
        if response.status_code != 200:
            data = Entry(key=key, value=LockFromClient(next_value=name, current_value="", end_of_lock=time.time() + time_locking, version=0))
            print(f"Send POST for lock with:    {data}")
            response = await client.post(cas_url, json=data.model_dump())
            
        else:
            found_entry = LockEntry(**response.json())
            while is_locked(found_entry):
                print("Try to lock...")
                await asyncio.sleep(2)
                response = await client.get(get_url)
                found_entry = LockEntry(**response.json())
            data = Entry(key=key, value=LockFromClient(next_value=name, current_value=found_entry.value, end_of_lock=time.time() + time_locking, version=found_entry.version))
            print(f"Unlocked! Try to lock with:    {data}")
            
        response = await client.post(cas_url, json=data.model_dump())
        if response.status_code != 200:
            print(f"An error occured while locking: {response.json()}")
            return
        
        for _ in range(0, time_locking, time_locking // 5):
            await asyncio.sleep(time_locking // 5)
            response = await client.get(get_url)
            print(f"Check '{key}' for locked: {is_mine(LockEntry(**response.json()), name)}")
            

# Аргументы: имя клиента, ключ, хост, время блокировки в сек
if __name__ == "__main__":
    args = sys.argv[1:]
    asyncio.run(main())
