"""Anthropic prompt-cache token pricing (issue #1986)."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_costs():
    path = Path(__file__).resolve().parents[1] / "gpt_researcher" / "utils" / "costs.py"
    spec = importlib.util.spec_from_file_location("gptr_costs_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_anthropic_cache_creation_tokens_increase_cost():
    costs = _load_costs()
    base = costs.calculate_llm_cost(
        llm_provider="anthropic",
        model="claude-sonnet-4-5",
        input_content="",
        output_content="",
        response_metadata={
            "model": "claude-sonnet-4-5",
            "usage": {"input_tokens": 50, "output_tokens": 300},
        },
    )
    with_cache = costs.calculate_llm_cost(
        llm_provider="anthropic",
        model="claude-sonnet-4-5",
        input_content="",
        output_content="",
        response_metadata={
            "model": "claude-sonnet-4-5",
            "usage": {
                "input_tokens": 50,
                "cache_creation_input_tokens": 4000,
                "cache_read_input_tokens": 0,
                "output_tokens": 300,
            },
        },
    )
    assert base == 0.00465
    assert abs(with_cache - 0.01965) < 1e-12
    assert with_cache > base


def test_anthropic_cache_read_tokens_increase_cost():
    costs = _load_costs()
    with_read = costs.calculate_llm_cost(
        llm_provider="anthropic",
        model="claude-sonnet-4-5",
        input_content="",
        output_content="",
        response_metadata={
            "model": "claude-sonnet-4-5",
            "usage": {
                "input_tokens": 50,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 4000,
                "output_tokens": 300,
            },
        },
    )
    assert abs(with_read - 0.00585) < 1e-12
