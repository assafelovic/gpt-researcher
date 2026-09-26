"""``llm_kwargs`` / ``LLM_KWARGS`` are the documented per-provider escape hatch. They must win over the
temperature ``create_chat_completion`` computes, or a provider that accepts exactly one temperature
(Moonshot's kimi-k3 rejects anything but 1) cannot be used at all."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gpt_researcher.utils.llm import create_chat_completion


async def _provider_kwargs(monkeypatch, **call_kwargs):
    monkeypatch.delenv("LLM_KWARGS", raising=False) if "env" not in call_kwargs else monkeypatch.setenv("LLM_KWARGS", call_kwargs.pop("env"))
    provider = MagicMock()
    provider.get_chat_response = AsyncMock(return_value="ok")
    with patch("gpt_researcher.utils.llm.get_llm", return_value=provider) as mock_get_llm:
        await create_chat_completion(
            messages=[{"role": "user", "content": "Generate a report"}],
            model="kimi-k3",
            llm_provider="openai",
            **call_kwargs,
        )
    return mock_get_llm.call_args.kwargs


@pytest.mark.asyncio
async def test_llm_kwargs_temperature_overrides_the_computed_one(monkeypatch):
    kwargs = await _provider_kwargs(monkeypatch, temperature=0.35, llm_kwargs={"temperature": 1})
    assert kwargs["temperature"] == 1


@pytest.mark.asyncio
async def test_env_llm_kwargs_temperature_overrides_the_computed_one(monkeypatch):
    kwargs = await _provider_kwargs(monkeypatch, temperature=0.35, env=json.dumps({"temperature": 1}))
    assert kwargs["temperature"] == 1


@pytest.mark.asyncio
async def test_computed_temperature_still_applies_without_an_override(monkeypatch):
    kwargs = await _provider_kwargs(monkeypatch, temperature=0.35)
    assert kwargs["temperature"] == 0.35


@pytest.mark.asyncio
async def test_llm_kwargs_still_override_other_computed_fields(monkeypatch):
    kwargs = await _provider_kwargs(monkeypatch, max_tokens=4000, llm_kwargs={"max_tokens": 64_000})
    assert kwargs["max_tokens"] == 64_000
