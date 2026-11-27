"""An empty answer cut off by the output limit is retried once with a larger
limit, then raised, instead of being resent unchanged up to 10 times.

Follow-up to #2251 / #2260. Offline: the provider is a mock.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gpt_researcher.utils.llm import create_chat_completion

MESSAGES = [{"role": "user", "content": "Summarize results"}]
OPENAI_CUT_OFF = {"finish_reason": "length"}
NOT_CUT_OFF = {"finish_reason": "stop"}


def make_provider(replies):
    """A mock provider that returns (text, response_metadata) pairs in order."""
    provider = MagicMock()
    provider.last_response_metadata = {}
    provider.last_usage_metadata = None
    replies = list(replies)

    async def get_chat_response(*_args, **_kwargs):
        text, metadata = replies.pop(0)
        provider.last_response_metadata = metadata
        return text

    provider.get_chat_response = AsyncMock(side_effect=get_chat_response)
    return provider


async def run(provider, max_tokens=8000, costs=None, **kwargs):
    with (
        patch("gpt_researcher.utils.llm.get_llm", return_value=provider) as get_llm,
        patch("gpt_researcher.utils.llm.calculate_llm_cost", return_value=0.01),
        patch("gpt_researcher.utils.llm.asyncio.sleep", new_callable=AsyncMock),
    ):
        try:
            result = await create_chat_completion(
                messages=MESSAGES,
                model="gpt-5.4",
                llm_provider="openai",
                max_tokens=max_tokens,
                cost_callback=costs.append if costs is not None else None,
                **kwargs,
            )
        except RuntimeError as exc:
            result = exc
    limits = [call.kwargs["max_tokens"] for call in get_llm.call_args_list]
    return result, limits


@pytest.mark.asyncio
async def test_cut_off_empty_answer_is_retried_once_with_double_limit():
    provider = make_provider([("", OPENAI_CUT_OFF), ("research result", NOT_CUT_OFF)])

    result, limits = await run(provider, max_tokens=8000)

    assert result == "research result"
    assert limits == [8000, 16000]
    assert provider.get_chat_response.await_count == 2


@pytest.mark.asyncio
async def test_cut_off_twice_raises_a_clear_error_after_two_attempts():
    provider = make_provider([("", OPENAI_CUT_OFF)] * 10)
    costs = []

    result, limits = await run(provider, max_tokens=4000, costs=costs)

    assert isinstance(result, RuntimeError)
    assert "max_tokens=8000" in str(result)
    assert "TOKEN_LIMIT" in str(result)
    assert limits == [4000, 8000]
    assert provider.get_chat_response.await_count == 2
    # Both attempts were billed, so both are counted.
    assert costs == [0.01, 0.01]


@pytest.mark.asyncio
async def test_larger_limit_is_capped_by_the_max_tokens_guard():
    provider = make_provider([("", OPENAI_CUT_OFF), ("ok", NOT_CUT_OFF)])

    result, limits = await run(provider, max_tokens=150_000)

    assert result == "ok"
    assert limits == [150_000, 200_000]


@pytest.mark.asyncio
async def test_cut_off_at_the_guard_raises_without_retrying():
    provider = make_provider([("", OPENAI_CUT_OFF)] * 10)

    result, limits = await run(provider, max_tokens=200_000)

    assert isinstance(result, RuntimeError)
    assert limits == [200_000]
    assert provider.get_chat_response.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "metadata",
    [
        {"stop_reason": "max_tokens"},  # Anthropic
        {"finish_reason": "MAX_TOKENS"},  # Gemini
        {"done_reason": "length"},  # Ollama
        {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}},  # OpenAI Responses API
    ],
)
async def test_cut_off_is_detected_for_other_providers(metadata):
    provider = make_provider([("", metadata), ("ok", {})])

    result, limits = await run(provider, max_tokens=8000)

    assert result == "ok"
    assert limits == [8000, 16000]


@pytest.mark.asyncio
async def test_empty_answer_that_was_not_cut_off_keeps_the_same_limit_and_retry():
    provider = make_provider([("", NOT_CUT_OFF), ("", {}), ("ok", NOT_CUT_OFF)])

    result, limits = await run(provider, max_tokens=8000)

    assert result == "ok"
    assert limits == [8000]
    assert provider.get_chat_response.await_count == 3


@pytest.mark.asyncio
async def test_first_attempt_is_unchanged():
    provider = make_provider([("first answer", NOT_CUT_OFF)])

    result, limits = await run(provider, max_tokens=8000)

    assert result == "first answer"
    assert limits == [8000]
    assert provider.get_chat_response.await_count == 1
