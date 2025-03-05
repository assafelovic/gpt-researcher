from __future__ import annotations

import asyncio

from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager


class WorkerPool:
    def __init__(self, max_workers: int):
        self.max_workers: int = max_workers
        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore: asyncio.Semaphore = asyncio.Semaphore(max_workers)

    @asynccontextmanager
    async def throttle(self):
        async with self.semaphore:
            yield
