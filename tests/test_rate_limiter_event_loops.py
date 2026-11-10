"""Global pacing survives independent event loops without reserving cancelled slots."""
import asyncio
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from itertools import pairwise
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import pytest


@pytest.fixture
def helpers():
    # Import the real helpers without importing optional LLM integrations.
    path = Path(__file__).resolve().parents[1] / "gpt_researcher" / "utils"
    package = ModuleType("gptr_pacing_test")
    package.__path__ = [str(path)]
    with patch.dict(sys.modules, {package.__name__: package}):
        from gptr_pacing_test import rate_limiter, workers
        yield rate_limiter, workers


async def batch(workers, count=4, delay=0.01):
    pool = workers.WorkerPool(count, delay)

    async def request():
        async with pool.throttle():
            return workers.get_global_rate_limiter().last_request_time

    try:
        return await asyncio.gather(*(request() for _ in range(count)))
    finally:
        pool.executor.shutdown(wait=True)


@pytest.fixture
def grants(helpers, monkeypatch):
    module, _ = helpers
    recorded = []
    original = module.GlobalRateLimiter.__setattr__

    def record(self, name, value):
        original(self, name, value)
        if name == "last_request_time":
            # Production assigns this while holding the grant lock. Recording
            # here avoids measuring delayed task/thread resumption as a grant.
            recorded.append(value)

    monkeypatch.setattr(module.GlobalRateLimiter, "__setattr__", record)
    return recorded


def assert_spaced(grants, delay):
    grants = sorted(grants)
    assert all(b - a >= delay - 1e-6 for a, b in pairwise(grants))


def test_new_worker_pools_in_sequential_loops(helpers, grants):
    _, workers = helpers
    asyncio.run(batch(workers))
    asyncio.run(batch(workers))
    assert len(grants) == 8
    assert_spaced(grants, 0.01)


def test_multiple_pools_share_spacing(helpers, grants):
    _, workers = helpers

    async def run():
        return await asyncio.gather(batch(workers), batch(workers))

    asyncio.run(run())
    assert len(grants) == 8
    assert_spaced(grants, 0.01)


def test_foreign_live_loop_is_rejected_before_lazy_binding(helpers):
    module, _ = helpers
    limiter = module.get_global_rate_limiter()
    limiter.configure(0.01)
    owner = asyncio.new_event_loop()
    try:
        # An uncontended lock has not lazily bound itself, but its explicit
        # owner must still prevent a second live loop from claiming it.
        owner.run_until_complete(limiter.wait_if_needed())
        with pytest.raises(RuntimeError, match="concurrent event loops"):
            asyncio.run(limiter.wait_if_needed())
        owner.run_until_complete(limiter.wait_if_needed())
    finally:
        owner.close()


def test_cancelled_wait_does_not_consume_a_slot(helpers, monkeypatch):
    module, _ = helpers
    limiter = module.get_global_rate_limiter()
    limiter.configure(10)
    now = [100.0]
    monkeypatch.setattr(module, "time", SimpleNamespace(time=lambda: now[0]))

    async def run():
        await limiter.wait_if_needed()
        sleeping = asyncio.Event()

        async def sleep(delay):
            sleeping.set()
            await asyncio.Future()

        monkeypatch.setattr(module, "asyncio", SimpleNamespace(sleep=sleep, Lock=asyncio.Lock, get_running_loop=asyncio.get_running_loop))
        pending = asyncio.create_task(limiter.wait_if_needed())
        await sleeping.wait()
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pending
        assert limiter.last_request_time == 100
        now[0] = 110
        await limiter.wait_if_needed()
        assert limiter.last_request_time == 110

    asyncio.run(run())


def test_fifo_waiters_sleep_once(helpers, monkeypatch):
    module, _ = helpers
    limiter = module.get_global_rate_limiter()
    limiter.configure(1)
    now = [100.0]
    sleeps = []
    completion = []
    real_sleep = asyncio.sleep
    monkeypatch.setattr(module, "time", SimpleNamespace(time=lambda: now[0]))

    async def sleep(delay):
        sleeps.append(delay)
        await real_sleep(0)
        now[0] += delay

    monkeypatch.setattr(module, "asyncio", SimpleNamespace(
        sleep=sleep, Lock=asyncio.Lock, get_running_loop=asyncio.get_running_loop
    ))

    async def request(i):
        await limiter.wait_if_needed()
        completion.append(i)

    async def run():
        await asyncio.gather(*(request(i) for i in range(30)))

    asyncio.run(run())
    assert completion == list(range(30))
    assert len(sleeps) == 29


def test_nan_delay_retains_existing_no_sleep_behavior(helpers):
    module, _ = helpers
    limiter = module.get_global_rate_limiter()
    limiter.configure(float("nan"))

    async def run():
        await asyncio.wait_for(limiter.wait_if_needed(), timeout=1)

    asyncio.run(run())


def test_zero_delay_across_loops(helpers):
    _, workers = helpers
    assert len(asyncio.run(batch(workers, delay=0))) == 4
    assert len(asyncio.run(batch(workers, delay=0))) == 4


def test_simultaneous_threads_cannot_claim_different_live_loops(helpers):
    module, _ = helpers
    limiter = module.get_global_rate_limiter()
    limiter.configure(0.01)
    start = threading.Barrier(2)
    finish = threading.Barrier(2)

    def run():
        loop = asyncio.new_event_loop()
        try:
            start.wait(timeout=5)
            try:
                loop.run_until_complete(limiter.wait_if_needed())
                result = "granted"
            except RuntimeError as exc:
                assert "concurrent event loops" in str(exc)
                result = "rejected"
            # Keep the owning loop alive until both acquisition attempts end.
            finish.wait(timeout=5)
            return result
        finally:
            loop.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run) for _ in range(2)]
        results = [future.result(timeout=10) for future in futures]
    assert sorted(results) == ["granted", "rejected"]
    asyncio.run(limiter.wait_if_needed())
