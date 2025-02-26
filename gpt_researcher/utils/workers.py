import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager


class WorkerPool:
    def __init__(self, max_workers: int):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers)

    @asynccontextmanager
    async def throttle(self):
        async with self.semaphore:
            yield
