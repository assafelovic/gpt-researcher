"""GlobalRateLimiter.configure must coerce/validate delay values."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

path = (
    Path(__file__).resolve().parents[1]
    / "gpt_researcher"
    / "utils"
    / "rate_limiter.py"
)
spec = importlib.util.spec_from_file_location("gptr_rate_limiter_ut", path)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
GlobalRateLimiter = mod.GlobalRateLimiter


def test_configure_coerces_string_delay():
    limiter = GlobalRateLimiter()
    limiter.reset()
    limiter.configure("0.25")
    assert limiter.rate_limit_delay == 0.25


def test_configure_none_is_zero():
    limiter = GlobalRateLimiter()
    limiter.configure(None)
    assert limiter.rate_limit_delay == 0.0


def test_configure_rejects_negative():
    limiter = GlobalRateLimiter()
    with pytest.raises(ValueError, match="non-negative"):
        limiter.configure(-1)


def test_configure_rejects_garbage():
    limiter = GlobalRateLimiter()
    with pytest.raises(ValueError):
        limiter.configure("fast")
