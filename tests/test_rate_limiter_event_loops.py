"""Global pacing works across sequential and concurrent event loops."""

import asyncio
import sys
import threading
import time
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
            return time.monotonic()

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
        if name == "last_request_time" and self._last_slot is not None:
            # Assigned while holding the reservation lock, before any sleep.
            recorded.append(value)

    monkeypatch.setattr(module.GlobalRateLimiter, "__setattr__", record)
    return recorded


def assert_spaced(grants, delay, completions=None):
    ordered_grants = sorted(grants)
    assert all(b - a >= delay - 1e-6 for a, b in pairwise(ordered_grants))
    if completions is not None:
        ordered_done = sorted(completions)
        assert len(ordered_done) == len(ordered_grants)
        assert all(
            done >= slot - 1e-6 for done, slot in zip(ordered_done, ordered_grants)
        )


def test_new_worker_pools_in_sequential_loops(helpers, grants):
    _, workers = helpers
    first = asyncio.run(batch(workers))
    second = asyncio.run(batch(workers))
    assert len(grants) == 8
    assert_spaced(grants, 0.01, first + second)


def test_multiple_pools_share_spacing(helpers, grants):
    _, workers = helpers

    async def run():
        first, second = await asyncio.gather(batch(workers), batch(workers))
        return first + second

    completions = asyncio.run(run())
    assert len(grants) == 8
    assert_spaced(grants, 0.01, completions)


def test_second_loop_works_while_first_loop_is_still_open(helpers, grants):
    module, _ = helpers
    limiter = module.get_global_rate_limiter()
    limiter.configure(0.01)
    owner = asyncio.new_event_loop()
    completions = []
    try:
        owner.run_until_complete(limiter.wait_if_needed())
        completions.append(time.monotonic())

        # A second loop must work without error even while the first is still open.
        asyncio.run(limiter.wait_if_needed())
        completions.append(time.monotonic())

        owner.run_until_complete(limiter.wait_if_needed())
        completions.append(time.monotonic())
    finally:
        owner.close()

    assert len(grants) == 3
    assert_spaced(grants, 0.01, completions)


def test_concurrent_worker_threads_preserve_monotonic_spacing(helpers, grants):
    _, workers = helpers
    delay = 0.015
    threads = 3
    per_thread = 3
    start = threading.Barrier(threads)

    def run_worker():
        start.wait(timeout=5)
        return asyncio.run(batch(workers, count=per_thread, delay=delay))

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(run_worker) for _ in range(threads)]
        completions = [t for future in futures for t in future.result(timeout=10)]

    expected_total = threads * per_thread
    assert len(grants) == expected_total
    assert_spaced(grants, delay, completions)
    assert max(completions) - min(grants) >= (expected_total - 1) * delay - 1e-6


def test_fifo_waiters_sleep_once(helpers, monkeypatch):
    module, _ = helpers
    limiter = module.get_global_rate_limiter()
    limiter.configure(1.0)
    now = [100.0]
    sleeps = []
    scheduled = []
    completion = []
    monkeypatch.setattr(module, "time", SimpleNamespace(monotonic=lambda: now[0]))

    async def fake_sleep(delay):
        sleeps.append(delay)
        gate = asyncio.Event()
        scheduled.append((now[0] + delay, len(scheduled), gate))
        await gate.wait()

    monkeypatch.setattr(module, "asyncio", SimpleNamespace(sleep=fake_sleep))

    async def request(i):
        await limiter.wait_if_needed()
        completion.append(i)

    async def run():
        tasks = [asyncio.create_task(request(i)) for i in range(30)]
        await asyncio.sleep(0)
        # Wake sleepers in scheduled timestamp order.
        for wake_at, _, gate in sorted(scheduled):
            now[0] = wake_at
            gate.set()
            await asyncio.sleep(0)
        await asyncio.gather(*tasks)

    asyncio.run(run())
    assert sleeps == [float(i) for i in range(1, 30)]
    assert completion == list(range(30))


def test_cancelled_wait_releases_tail_slot_only(helpers, monkeypatch):
    module, _ = helpers
    limiter = module.get_global_rate_limiter()
    limiter.configure(10.0)
    now = [100.0]
    sleeps = []
    monkeypatch.setattr(module, "time", SimpleNamespace(monotonic=lambda: now[0]))

    async def run():
        # First request claims 100.0 with no sleep.
        await limiter.wait_if_needed()
        assert limiter.last_request_time == 100.0

        sleeping = asyncio.Event()

        async def blocking_sleep(delay):
            sleeps.append(delay)
            sleeping.set()
            await asyncio.Future()

        monkeypatch.setattr(module, "asyncio", SimpleNamespace(sleep=blocking_sleep))

        # Tail cancellation restores the previous slot.
        tail = asyncio.create_task(limiter.wait_if_needed())
        await sleeping.wait()
        assert sleeps == [10.0]
        tail.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tail
        assert limiter.last_request_time == 100.0

        # Once 10s elapse, the next request proceeds immediately with no sleep.
        now[0] = 110.0
        await limiter.wait_if_needed()
        assert limiter.last_request_time == 110.0
        assert sleeps == [10.0]

        # Non-tail cancellation must not roll back a later waiter's reservation.
        sleeps.clear()
        sleeping.clear()
        first_waiter = asyncio.create_task(limiter.wait_if_needed())
        await sleeping.wait()
        sleeping.clear()
        second_waiter = asyncio.create_task(limiter.wait_if_needed())
        await sleeping.wait()
        assert sleeps == [10.0, 20.0]

        first_waiter.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first_waiter
        assert limiter.last_request_time == 130.0

        sleeping.clear()
        third_waiter = asyncio.create_task(limiter.wait_if_needed())
        await sleeping.wait()
        assert sleeps == [10.0, 20.0, 30.0]

        for task in (second_waiter, third_waiter):
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(run())


def test_reconfiguring_delay_takes_effect_immediately(helpers, monkeypatch):
    module, _ = helpers
    limiter = module.get_global_rate_limiter()
    now = [100.0]
    sleeps = []
    monkeypatch.setattr(module, "time", SimpleNamespace(monotonic=lambda: now[0]))

    async def record_sleep(delay):
        sleeps.append(delay)
        now[0] += delay

    monkeypatch.setattr(module, "asyncio", SimpleNamespace(sleep=record_sleep))

    async def run():
        limiter.configure(10.0)
        await limiter.wait_if_needed()
        assert sleeps == []

        # Lowering delay should not inherit the old 10s gap.
        limiter.configure(0.01)
        now[0] = 100.5
        await limiter.wait_if_needed()
        assert sleeps == []

        # Raising delay should enforce the new spacing from the last request.
        limiter.configure(5.0)
        now[0] = 101.0
        await limiter.wait_if_needed()
        assert sleeps == [pytest.approx(4.5)]

    asyncio.run(run())


def test_zero_and_nan_delay_do_not_sleep_across_loops(helpers, monkeypatch):
    module, workers = helpers
    limiter = module.get_global_rate_limiter()
    sleeps = []

    async def fail_sleep(delay):
        sleeps.append(delay)
        raise AssertionError(f"unexpected sleep({delay})")

    monkeypatch.setattr(module, "asyncio", SimpleNamespace(sleep=fail_sleep))

    assert len(asyncio.run(batch(workers, delay=0))) == 4
    assert len(asyncio.run(batch(workers, delay=0))) == 4

    limiter.configure(float("nan"))
    asyncio.run(asyncio.wait_for(limiter.wait_if_needed(), timeout=1))
    assert sleeps == []

    # NaN must not poison subsequent positive delays.
    limiter.configure(0.01)
    asyncio.run(limiter.wait_if_needed())
    assert sleeps == []


def test_reset_and_negative_monotonic_clock(helpers, monkeypatch):
    module, _ = helpers
    limiter = module.get_global_rate_limiter()
    limiter.configure(10.0)
    now = [-50.0]
    sleeps = []
    monkeypatch.setattr(module, "time", SimpleNamespace(monotonic=lambda: now[0]))

    async def record_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(module, "asyncio", SimpleNamespace(sleep=record_sleep))

    async def run():
        # First request at a negative monotonic value must not sleep.
        await limiter.wait_if_needed()
        assert sleeps == []

        limiter.reset()
        assert limiter.last_request_time == 0.0

        # Next request after reset also proceeds immediately.
        await limiter.wait_if_needed()
        assert sleeps == []

    asyncio.run(run())
