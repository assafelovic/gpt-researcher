from __future__ import annotations

import asyncio
import os

from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator


class WorkerPool:
    def __init__(self, max_workers: int):
        self.max_workers: int = max_workers
        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore: asyncio.Semaphore = asyncio.Semaphore(max_workers)

    @asynccontextmanager
    async def throttle(
        self,
    ) -> AsyncGenerator[Any, None]:
        async with self.semaphore:
            yield
