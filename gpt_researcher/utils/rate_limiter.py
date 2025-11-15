"""
Global rate limiter for scraper requests.

Ensures that SCRAPER_RATE_LIMIT_DELAY is enforced globally across ALL WorkerPools,
not just per-pool. This prevents multiple concurrent researchers from overwhelming
rate-limited APIs like Firecrawl.
"""
import asyncio
import time
from typing import ClassVar


class GlobalRateLimiter:
    """
    Singleton global rate limiter.

    Ensures minimum delay between ANY scraper requests across the entire application,
    regardless of how many WorkerPools or GPTResearcher instances are active.
    """

    _instance: ClassVar['GlobalRateLimiter'] = None
    _lock: ClassVar[asyncio.Lock] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the global rate limiter (only once)."""
        if self._initialized:
            return

        self.last_request_time = 0.0
        self.rate_limit_delay = 0.0
        self._initialized = True

        # Create lock at class level to ensure it's shared across all instances
        if GlobalRateLimiter._lock is None:
            # Note: This will be properly initialized when first accessed in an async context
            GlobalRateLimiter._lock = None

    @classmethod
    def get_lock(cls):
        """Get or create the async lock (must be called from async context)."""
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    def configure(self, rate_limit_delay: float):
        """
        Configure the global rate limit delay.

        Args:
            rate_limit_delay: Minimum seconds between requests (0 = no limit)
        """
        self.rate_limit_delay = rate_limit_delay

    async def wait_if_needed(self):
        """
        Wait if needed to enforce global rate limiting.

        This method ensures that regardless of how many WorkerPools are active,
        the SCRAPER_RATE_LIMIT_DELAY is respected globally.
        """
        if self.rate_limit_delay <= 0:
            return  # No rate limiting

        lock = self.get_lock()
        async with lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time

            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                await asyncio.sleep(sleep_time)

            self.last_request_time = time.time()

    def reset(self):
        """Reset the rate limiter state (useful for testing)."""
        self.last_request_time = 0.0


# Singleton instance
_global_rate_limiter = GlobalRateLimiter()


def get_global_rate_limiter() -> GlobalRateLimiter:
    """Get the global rate limiter singleton instance."""
    return _global_rate_limiter
