"""A WorkerPool that asks for no rate limit must not clear the global one.

The rate limiter is a process-wide singleton shared by every WorkerPool (that is the
point: deep research builds several researchers, each with its own pool). A pool
constructed with the default `rate_limit_delay=0` used to overwrite the shared delay
with 0, silently disabling the limit that another pool had configured.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

utils_dir = Path(__file__).resolve().parents[1] / "gpt_researcher" / "utils"
pkg_name = "gptr_utils_worker_pool_ut"
pkg = types.ModuleType(pkg_name)
pkg.__path__ = [str(utils_dir)]
sys.modules[pkg_name] = pkg


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"{pkg_name}.{name}", utils_dir / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rate_limiter = _load("rate_limiter")
workers = _load("workers")


def _cleanup(*pools, limiter) -> None:
    for pool in pools:
        pool.executor.shutdown(wait=False)
    limiter.configure(0)
    for name in ("workers", "rate_limiter"):
        sys.modules.pop(f"{pkg_name}.{name}", None)
    sys.modules.pop(pkg_name, None)


def test_pool_without_a_delay_keeps_the_configured_global_delay():
    limiter = rate_limiter.get_global_rate_limiter()
    limiter.configure(6.5)  # e.g. Firecrawl free tier: 10 requests per minute

    limited = workers.WorkerPool(max_workers=1, rate_limit_delay=6.5)
    default = workers.WorkerPool(max_workers=1)
    try:
        assert default.rate_limit_delay == 0
        assert limiter.rate_limit_delay == 6.5
    finally:
        _cleanup(limited, default, limiter=limiter)


def test_pool_with_a_delay_still_configures_the_global_limiter():
    limiter = rate_limiter.get_global_rate_limiter()
    limiter.configure(0)

    limited = workers.WorkerPool(max_workers=1, rate_limit_delay=2.5)
    try:
        assert limiter.rate_limit_delay == 2.5
    finally:
        _cleanup(limited, limiter=limiter)
