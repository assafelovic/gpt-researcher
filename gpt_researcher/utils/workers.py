import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class WorkerPool:
    """Thread pool with rate limiting for concurrent operations."""
    
    def __init__(self, max_workers: int):
        """Initialize worker pool with specified max workers.
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="gptr-worker"
        )
        self.semaphore = asyncio.Semaphore(max_workers)
        self._active_tasks = 0
        self._completed_tasks = 0
        logger.info(f"Initialized WorkerPool with {max_workers} workers")

    @asynccontextmanager
    async def throttle(self):
        """Throttle concurrent operations using semaphore."""
        async with self.semaphore:
            self._active_tasks += 1
            try:
                yield
            finally:
                self._active_tasks -= 1
                self._completed_tasks += 1
    
    def shutdown(self, wait: bool = True):
        """Shutdown the thread pool executor.
        
        Args:
            wait: Whether to wait for pending tasks to complete
        """
        logger.info(f"Shutting down WorkerPool (completed: {self._completed_tasks} tasks)")
        self.executor.shutdown(wait=wait)
    
    @property
    def stats(self) -> dict:
        """Get worker pool statistics."""
        return {
            "max_workers": self.max_workers,
            "active_tasks": self._active_tasks,
            "completed_tasks": self._completed_tasks
        }
