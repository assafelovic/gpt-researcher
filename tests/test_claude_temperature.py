"""Claude Opus 4.7 and later, the Claude 5 family, Fable and Mythos reject ``temperature`` with a 400, so
``create_chat_completion`` must not send it for them, whatever prefix the provider puts on the model id."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gpt_researcher.utils.llm import create_chat_completion


async def _temperature_sent(monkeypatch, model):
    monkeypatch.delenv("LLM_KWARGS", raising=False)
    provider = MagicMock()
    provider.get_chat_response = AsyncMock(return_value="ok")
    with patch("gpt_researcher.utils.llm.get_llm", return_value=provider) as mock_get_llm:
        await create_chat_completion(
            messages=[{"role": "user", "content": "Generate a report"}],
            model=model,
            llm_provider="anthropic",
            temperature=0.4,
        )
    return mock_get_llm.call_args.kwargs["temperature"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "model",
    [
        "claude-opus-4-8",
        "claude-opus-5",
        "claude-opus-5-5",
        "claude-sonnet-5",
        "claude-sonnet-5-5",
        "claude-haiku-5-5",
        "claude-fable-5-1",
        "anthropic.claude-opus-5-5",
        "us.anthropic.claude-opus-4-7-v1:0",
        "anthropic/claude-sonnet-5",
    ],
)
async def test_claude_models_that_reject_temperature_get_none(monkeypatch, model):
    assert await _temperature_sent(monkeypatch, model) is None


@pytest.mark.asyncio
async def test_models_that_accept_temperature_still_get_it(monkeypatch):
    assert await _temperature_sent(monkeypatch, "gpt-4.1") == 0.4
