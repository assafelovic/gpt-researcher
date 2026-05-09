"""
Task Manager — persistent research task queue.

Decouples task execution from WebSocket lifecycle so that:
  - Page refresh / WS disconnect does NOT cancel the running task.
  - Multiple tasks can be queued and run one at a time (configurable).
  - Frontend can poll task status and reconnect to the log stream at any time.

Usage:
    from server.task_manager import task_manager

    # Startup (call from FastAPI lifespan):
    task_manager.start(max_workers=1)

    # Submit a task:
    task_id = await task_manager.submit(params_dict)

    # Poll:
    task = task_manager.get(task_id)
    print(task.status, task.logs[-5:])

    # Stream logs via WebSocket:
    q = await task_manager.subscribe(task_id)
    # ... send q items to ws ...
    task_manager.unsubscribe(task_id, q)
"""

import asyncio
import logging
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchTask:
    def __init__(self, task_id: str, params: dict):
        self.task_id = task_id
        self.params = params
        self.status: TaskStatus = TaskStatus.QUEUED
        self.logs: List[dict] = []           # All log messages — survives WS disconnect
        self.file_paths: Optional[dict] = None   # {pdf, docx, md, json}
        self.error: Optional[str] = None
        self.created_at: float = time.time()
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        # Subscriber queues — each connected WebSocket gets one
        self._subscribers: List[asyncio.Queue] = []

    def summary(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "query": self.params.get("task", ""),
            "report_type": self.params.get("report_type", ""),
            "report_source": self.params.get("report_source", ""),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "log_count": len(self.logs),
            "file_paths": self.file_paths,
            "error": self.error,
        }


class TaskManager:
    """Global task queue with asyncio worker(s)."""

    def __init__(self):
        self._tasks: Dict[str, ResearchTask] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_tasks: List[asyncio.Task] = []
        self._max_workers: int = 1

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, max_workers: int = 1):
        """Start background worker(s). Call once from FastAPI lifespan."""
        self._max_workers = max_workers
        for _ in range(max_workers):
            t = asyncio.create_task(self._worker())
            self._worker_tasks.append(t)
        logger.info(f"TaskManager started with {max_workers} worker(s)")

    async def stop(self):
        """Graceful shutdown."""
        for t in self._worker_tasks:
            t.cancel()
        self._worker_tasks.clear()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def submit(self, params: dict) -> str:
        """Enqueue a research task. Returns task_id immediately."""
        task_id = uuid.uuid4().hex[:12]
        task = ResearchTask(task_id, params)
        self._tasks[task_id] = task
        await self._queue.put(task_id)
        logger.info(f"Task {task_id} queued: {params.get('task', '')[:60]}")
        return task_id

    def get(self, task_id: str) -> Optional[ResearchTask]:
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[dict]:
        tasks = sorted(self._tasks.values(), key=lambda t: t.created_at, reverse=True)
        return [t.summary() for t in tasks]

    async def subscribe(self, task_id: str) -> Optional[asyncio.Queue]:
        """
        Subscribe to a task's log stream.
        Replays all existing logs immediately, then delivers new ones as they arrive.
        Returns None if task not found.
        """
        task = self._tasks.get(task_id)
        if task is None:
            return None
        q: asyncio.Queue = asyncio.Queue()
        # Replay existing logs
        for log in task.logs:
            await q.put(log)
        # If already done, send final status immediately
        if task.status in (TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELLED):
            await q.put({"type": "task_status", "status": task.status, "task_id": task_id,
                         "file_paths": task.file_paths, "error": task.error})
        else:
            task._subscribers.append(q)
        return q

    def unsubscribe(self, task_id: str, q: asyncio.Queue):
        task = self._tasks.get(task_id)
        if task and q in task._subscribers:
            task._subscribers.remove(q)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _broadcast(self, task: ResearchTask, message: dict):
        """Store log message and fan out to all active subscribers."""
        task.logs.append(message)
        dead = []
        for q in task._subscribers:
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            if q in task._subscribers:
                task._subscribers.remove(q)

    async def _worker(self):
        """Worker loop — picks tasks from queue and runs them sequentially."""
        while True:
            try:
                task_id = await self._queue.get()
                task = self._tasks.get(task_id)
                if task is None:
                    continue
                if task.status == TaskStatus.CANCELLED:
                    continue
                await self._run_task(task)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)

    async def _run_task(self, task: ResearchTask):
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        logger.info(f"Task {task.task_id} starting")

        try:
            # Import here to avoid circular imports
            from server.task_runner import run_research_task
            file_paths = await run_research_task(task, self._broadcast)
            task.file_paths = file_paths
            task.status = TaskStatus.DONE
            logger.info(f"Task {task.task_id} done")
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            logger.info(f"Task {task.task_id} cancelled")
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Task {task.task_id} failed: {e}", exc_info=True)
        finally:
            task.finished_at = time.time()
            # Notify all subscribers that task finished
            final_msg = {
                "type": "task_status",
                "status": task.status,
                "task_id": task.task_id,
                "file_paths": task.file_paths,
                "error": task.error,
            }
            for q in list(task._subscribers):
                try:
                    q.put_nowait(final_msg)
                except Exception:
                    pass
            # Drain subscriber list — task is done
            task._subscribers.clear()


# Singleton
task_manager = TaskManager()
