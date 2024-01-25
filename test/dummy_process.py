import asyncio


async def run():
    for _ in range(5):
        print("Sleepy sleepy")
        await asyncio.sleep(1)


asyncio.run(run())
