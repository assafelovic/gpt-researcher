import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from .rate_limiter import get_global_rate_limiter


class WorkerPool:
    def __init__(self, max_workers: int, rate_limit_delay: float = 0.0):
        """
        Initialize WorkerPool with concurrency and rate limiting.

        Args:
            max_workers: Maximum number of concurrent workers
            rate_limit_delay: Minimum seconds between requests GLOBALLY (0 = no limit)
                             This delay is enforced across ALL WorkerPools to prevent
                             overwhelming rate-limited APIs.
                             Example: 6.0 for 10 req/min (Firecrawl free tier)

        Note:
            The rate_limit_delay is enforced GLOBALLY using a singleton rate limiter.
            This means if you have multiple GPTResearcher instances (e.g., in deep research),
            they will all share the same rate limit, preventing API overload.
        """
        self.max_workers = max_workers
        self.rate_limit_delay = rate_limit_delay
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers)

        # Configure the global rate limiter
        # All WorkerPools share the same rate limiter instance
        global_limiter = get_global_rate_limiter()
        global_limiter.configure(rate_limit_delay)

    @asynccontextmanager
    async def throttle(self):
        """
        Throttle requests with both concurrency limiting and GLOBAL rate limiting.

        - Semaphore controls concurrent operations within THIS pool (how many at once)
        - Global rate limiter controls request frequency ACROSS ALL POOLS (global timing)

        This ensures that even with multiple concurrent GPTResearcher instances
        (e.g., in deep research), the total request rate stays within limits.
        """
        async with self.semaphore:
            # Use global rate limiter (shared across all WorkerPools)
            global_limiter = get_global_rate_limiter()
            await global_limiter.wait_if_needed()
            yield
