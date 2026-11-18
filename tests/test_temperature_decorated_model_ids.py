"""``supports_temperature`` must recognise a model whatever decoration the provider
put on its id.

``NO_SUPPORT_TEMPERATURE_MODELS`` is keyed by bare model id, but OpenRouter and
LiteLLM require a ``vendor/`` prefix (``openai/gpt-5``,
``anthropic/claude-sonnet-4-5``) and Bedrock appends a version suffix
(``us.anthropic.claude-sonnet-4-5-20250929-v1:0``). Matching the exact list
against the raw id missed all of them, so ``create_chat_completion`` sent a
``temperature`` the provider rejects with a 400 - which fails the call after the
retry budget instead of degrading.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gpt_researcher.llm_provider.generic.base import supports_temperature
from gpt_researcher.utils.llm import create_chat_completion


async def _temperature_sent(monkeypatch, model):
    monkeypatch.delenv("LLM_KWARGS", raising=False)
    provider = MagicMock()
    provider.get_chat_response = AsyncMock(return_value="ok")
    with patch("gpt_researcher.utils.llm.get_llm", return_value=provider) as mock_get_llm:
        await create_chat_completion(
            messages=[{"role": "user", "content": "Generate a report"}],
            model=model,
            llm_provider="openrouter",
            temperature=0.4,
        )
    return mock_get_llm.call_args.kwargs["temperature"]


@pytest.mark.parametrize(
    "model",
    [
        # OpenRouter / LiteLLM style prefix
        "anthropic/claude-sonnet-4-5",
        "openai/gpt-5",
        "anthropic/claude-opus-4-5",
        "openai/o3-mini",
        # Bedrock style prefix + version suffix
        "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "anthropic.claude-haiku-4-5-20251001-v1:0",
        # bare ids keep working
        "claude-sonnet-4-5",
        "gpt-5",
    ],
)
def test_decorated_ids_of_no_temperature_models_are_recognised(model):
    assert supports_temperature(model) is False


@pytest.mark.asyncio
@pytest.mark.parametrize("model", ["anthropic/claude-sonnet-4-5", "us.anthropic.claude-sonnet-4-5-20250929-v1:0"])
async def test_no_temperature_is_sent_for_decorated_ids(monkeypatch, model):
    assert await _temperature_sent(monkeypatch, model) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("model", ["gpt-4.1", "anthropic/claude-3-5-haiku", "mistral-large-latest"])
async def test_models_that_accept_temperature_still_get_it(monkeypatch, model):
    assert await _temperature_sent(monkeypatch, model) == 0.4
