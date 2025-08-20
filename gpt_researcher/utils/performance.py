"""
Performance monitoring and optimization utilities for GPT Researcher.
"""

import asyncio
import time
import logging
from typing import Any, Dict, Optional, Callable
from functools import wraps
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self):
        self.metrics = {
            "api_calls": 0,
            "api_total_time": 0.0,
            "scraping_calls": 0,
            "scraping_total_time": 0.0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        self._start_time = time.time()
    
    def record_api_call(self, duration: float, tokens: int = 0, cost: float = 0.0):
        """Record an API call metric."""
        self.metrics["api_calls"] += 1
        self.metrics["api_total_time"] += duration
        self.metrics["total_tokens"] += tokens
        self.metrics["total_cost"] += cost
    
    def record_scraping(self, duration: float):
        """Record a scraping operation metric."""
        self.metrics["scraping_calls"] += 1
        self.metrics["scraping_total_time"] += duration
    
    def record_cache_hit(self):
        """Record a cache hit."""
        self.metrics["cache_hits"] += 1
    
    def record_cache_miss(self):
        """Record a cache miss."""
        self.metrics["cache_misses"] += 1
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        elapsed = time.time() - self._start_time
        cache_total = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_rate = (self.metrics["cache_hits"] / cache_total * 100) if cache_total > 0 else 0
        
        return {
            "elapsed_time": elapsed,
            "api_calls": self.metrics["api_calls"],
            "avg_api_time": (self.metrics["api_total_time"] / self.metrics["api_calls"]) 
                           if self.metrics["api_calls"] > 0 else 0,
            "scraping_calls": self.metrics["scraping_calls"],
            "avg_scraping_time": (self.metrics["scraping_total_time"] / self.metrics["scraping_calls"])
                                if self.metrics["scraping_calls"] > 0 else 0,
            "total_tokens": self.metrics["total_tokens"],
            "total_cost": self.metrics["total_cost"],
            "cache_hit_rate": cache_rate
        }
    
    def log_summary(self):
        """Log performance summary."""
        stats = self.stats
        logger.info("=== Performance Summary ===")
        logger.info(f"Total time: {stats['elapsed_time']:.2f}s")
        logger.info(f"API calls: {stats['api_calls']} (avg: {stats['avg_api_time']:.2f}s)")
        logger.info(f"Scraping: {stats['scraping_calls']} (avg: {stats['avg_scraping_time']:.2f}s)")
        logger.info(f"Tokens used: {stats['total_tokens']}")
        logger.info(f"Total cost: ${stats['total_cost']:.4f}")
        logger.info(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")


def async_timed(name: Optional[str] = None):
    """Decorator to time async functions."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                func_name = name or func.__name__
                logger.debug(f"{func_name} completed in {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start
                func_name = name or func.__name__
                logger.error(f"{func_name} failed after {duration:.2f}s: {e}")
                raise
        return wrapper
    return decorator


@asynccontextmanager
async def measure_time(operation: str):
    """Context manager to measure operation time."""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        logger.debug(f"{operation} took {duration:.2f}s")


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, calls_per_second: float = 10.0):
        """Initialize rate limiter.
        
        Args:
            calls_per_second: Maximum calls per second
        """
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a call."""
        async with self._lock:
            current = time.time()
            time_since_last = current - self.last_call
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                await asyncio.sleep(sleep_time)
            
            self.last_call = time.time()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
