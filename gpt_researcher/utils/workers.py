import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager


class WorkerPool:
    def __init__(self, max_workers: int, rate_limit_delay: float = 0.0):
        """
        Initialize WorkerPool with concurrency and rate limiting.

        Args:
            max_workers: Maximum number of concurrent workers
            rate_limit_delay: Minimum seconds between requests (0 = no limit)
                             Useful for API rate limiting (e.g., 6.0 for 10 req/min)
        """
        self.max_workers = max_workers
        self.rate_limit_delay = rate_limit_delay
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers)
        self.last_request_time = 0.0  # Track last request for rate limiting
        self.rate_limit_lock = asyncio.Lock()  # Ensure thread-safe timing

    @asynccontextmanager
    async def throttle(self):
        """
        Throttle requests with both concurrency limiting and rate limiting.

        - Semaphore controls concurrent operations (how many at once)
        - Rate limiting controls request frequency (how many per time period)
        """
        async with self.semaphore:
            # Apply rate limiting if configured
            if self.rate_limit_delay > 0:
                async with self.rate_limit_lock:
                    current_time = time.time()
                    time_since_last = current_time - self.last_request_time

                    if time_since_last < self.rate_limit_delay:
                        sleep_time = self.rate_limit_delay - time_since_last
                        await asyncio.sleep(sleep_time)

                    self.last_request_time = time.time()

            yield
