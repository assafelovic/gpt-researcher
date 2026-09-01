"""choose_agent hot path should parse fenced agent JSON via json_repair."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from gpt_researcher.actions.agent_creator import choose_agent


@pytest.mark.asyncio
async def test_choose_agent_accepts_fenced_json():
    cfg = SimpleNamespace(
        smart_llm_model="m",
        smart_llm_provider="p",
        llm_kwargs={},
    )
    family = SimpleNamespace(auto_agent_instructions=lambda: "sys")
    fenced = """```json
{"server": "Research", "agent_role_prompt": "dig deep"}
```"""

    with patch(
        "gpt_researcher.actions.agent_creator.create_chat_completion",
        new=AsyncMock(return_value=fenced),
    ):
        server, role = await choose_agent(
            "q",
            cfg,
            cost_callback=None,
            prompt_family=family,
        )

    assert server == "Research"
    assert role == "dig deep"


@pytest.mark.asyncio
async def test_choose_agent_accepts_trailing_comma_json():
    cfg = SimpleNamespace(
        smart_llm_model="m",
        smart_llm_provider="p",
        llm_kwargs={},
    )
    family = SimpleNamespace(auto_agent_instructions=lambda: "sys")
    body = '{"server": "Ops", "agent_role_prompt": "run ops",}'

    with patch(
        "gpt_researcher.actions.agent_creator.create_chat_completion",
        new=AsyncMock(return_value=body),
    ):
        server, role = await choose_agent(
            "q",
            cfg,
            cost_callback=None,
            prompt_family=family,
        )

    assert server == "Ops"
    assert role == "run ops"
