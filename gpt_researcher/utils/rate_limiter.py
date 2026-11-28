"""
Global rate limiter for scraper requests.

Ensures that SCRAPER_RATE_LIMIT_DELAY is enforced globally across ALL WorkerPools,
not just per-pool. This prevents multiple concurrent researchers from overwhelming
rate-limited APIs like Firecrawl.
"""

import asyncio
import threading
import time
from typing import ClassVar


class GlobalRateLimiter:
    """
    Singleton global rate limiter.

    Ensures minimum delay between ANY scraper requests across the entire application,
    regardless of how many WorkerPools, GPTResearcher instances, or event loops
    are active.
    """

    _instance: ClassVar["GlobalRateLimiter | None"] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self):
        """Initialize the global rate limiter (only once)."""
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return

            self._last_slot: float | None = None
            self._slot_version = 0
            self.last_request_time = 0.0
            self.rate_limit_delay = 0.0
            self._initialized = True

    def configure(self, rate_limit_delay: float):
        """
        Configure the global rate limit delay.

        Args:
            rate_limit_delay: Minimum seconds between requests (0 = no limit)
        """
        # Env/config may hand us strings; wait_if_needed compares as float.
        if rate_limit_delay is None:
            delay = 0.0
        else:
            try:
                delay = float(rate_limit_delay)
            except (TypeError, ValueError) as e:
                raise ValueError(
                    f"rate_limit_delay must be a number, got {rate_limit_delay!r}"
                ) from e
            if delay < 0:
                raise ValueError(f"rate_limit_delay must be non-negative, got {delay}")
        with self._lock:
            self.rate_limit_delay = delay

    async def wait_if_needed(self):
        """
        Wait if needed to enforce global rate limiting.

        Reserves the next monotonic request slot under a thread lock and sleeps
        outside the lock on the caller's event loop, so spacing is preserved
        across sequential and concurrent event loops.
        """
        with self._lock:
            delay = self.rate_limit_delay
            if not (delay > 0):
                return  # No rate limiting

            now = time.monotonic()
            prev_slot = self._last_slot
            slot = now if prev_slot is None else max(now, prev_slot + delay)
            self._last_slot = slot
            self.last_request_time = slot
            self._slot_version += 1
            version = self._slot_version
            wait_time = slot - now

        if wait_time > 0:
            try:
                await asyncio.sleep(wait_time)
            except BaseException:
                with self._lock:
                    if self._slot_version == version:
                        self._last_slot = prev_slot
                        self.last_request_time = 0.0 if prev_slot is None else prev_slot
                        self._slot_version += 1
                raise

    def reset(self):
        """Reset the rate limiter state (useful for testing)."""
        with self._lock:
            self._last_slot = None
            self.last_request_time = 0.0
            self._slot_version += 1


# Singleton instance
_global_rate_limiter = GlobalRateLimiter()


def get_global_rate_limiter() -> GlobalRateLimiter:
    """Get the global rate limiter singleton instance."""
    return _global_rate_limiter
