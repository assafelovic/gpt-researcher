"""Regression: handle_json_error must not KeyError on partial agent JSON.

json.loads / json_repair can return non-dicts (list, str, null) or dicts
missing agent_role_prompt. The recovery path must fall back to the default
agent instead of raising.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import ModuleType

import pytest


def _load_agent_creator():
    path = (
        Path(__file__).resolve().parents[1]
        / "gpt_researcher"
        / "actions"
        / "agent_creator.py"
    )
    src = path.read_text()
    src = src.replace("from ..prompts import PromptFamily\n", "")
    src = src.replace("from ..utils.llm import create_chat_completion\n", "")
    mod = ModuleType("agent_creator_under_test")
    ns = mod.__dict__
    ns["PromptFamily"] = type("PromptFamily", (), {})
    ns["create_chat_completion"] = None
    exec(compile(src, str(path), "exec"), ns)
    return mod


@pytest.fixture(scope="module")
def agent_creator():
    return _load_agent_creator()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        None,
        "not json",
        "[]",
        "null",
        '"x"',
        "123",
        '{"server":"only-server"}',
        '{"agent_role_prompt":"only-role"}',
    ],
)
async def test_handle_json_error_falls_back_without_raise(agent_creator, response):
    server, role = await agent_creator.handle_json_error(response)
    assert server == "Default Agent"
    assert "research assistant" in role


@pytest.mark.asyncio
async def test_handle_json_error_accepts_valid_repaired_shape(agent_creator):
    server, role = await agent_creator.handle_json_error(
        '{"server":"Finance Agent","agent_role_prompt":"Analyze markets"}'
    )
    assert server == "Finance Agent"
    assert role == "Analyze markets"


def test_without_fix_partial_dict_keyerrors(agent_creator):
    """Document pre-fix failure mode on the regex path using bare json.loads semantics."""
    import json

    payload = json.loads('{"server":"only-server"}')
    # Pre-fix path: payload["agent_role_prompt"] KeyError
    with pytest.raises(KeyError):
        _ = payload["server"], payload["agent_role_prompt"]
