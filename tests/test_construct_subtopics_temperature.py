"""Detailed reports build subtopics in ``construct_subtopics``, which used to send
``temperature`` for every model that is not in ``SUPPORT_REASONING_EFFORT_MODELS``.

Claude 5, gpt-5 and the other models for which ``supports_temperature`` is false
reject that parameter. ``create_chat_completion`` already withholds it; this path
did not, so the provider returned 400 and the ``except`` handler gave back the
previous subtopics with no error to the caller.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.runnables import RunnableLambda

from gpt_researcher.utils.llm import construct_subtopics


def _config(model, temperature=0.25):
    return SimpleNamespace(
        smart_llm_model=model,
        smart_llm_provider="anthropic",
        temperature=temperature,
        smart_token_limit=4000,
        max_subtopics=3,
        llm_kwargs=None,
    )


def _provider():
    # A real runnable so the prompt | model | parser chain finishes. The
    # assertion is on the kwargs given to get_llm, which are fixed before
    # the chain runs.
    provider = MagicMock()
    provider.llm = RunnableLambda(
        lambda _prompt: '{"subtopics": [{"task": "indexes"}]}'
    )
    return provider


async def _temperature_sent(model):
    with patch("gpt_researcher.utils.llm.get_llm", return_value=_provider()) as mock_get_llm:
        await construct_subtopics(
            task="compare storage engines",
            data="context",
            config=_config(model),
            subtopics=["existing"],
        )
    return mock_get_llm.call_args.kwargs["temperature"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "model",
    [
        "claude-opus-4-8",
        "claude-opus-5",
        "claude-sonnet-5",
        "claude-haiku-5-5",
        "claude-fable-5",
        "anthropic/claude-sonnet-5",
        "us.anthropic.claude-opus-4-7-v1:0",
        "claude-sonnet-4-5",
        "gpt-5",
        "o1",
        "deepseek/deepseek-reasoner",
    ],
)
async def test_construct_subtopics_omits_temperature_when_unsupported(model):
    assert await _temperature_sent(model) is None


@pytest.mark.asyncio
async def test_construct_subtopics_still_sends_temperature_when_supported():
    assert await _temperature_sent("gpt-4.1") == 0.25


@pytest.mark.asyncio
async def test_construct_subtopics_reasoning_models_keep_effort_and_no_temperature():
    with patch("gpt_researcher.utils.llm.get_llm", return_value=_provider()) as mock_get_llm:
        await construct_subtopics(
            task="compare storage engines",
            data="context",
            config=_config("o3"),
            subtopics=[],
        )
    kwargs = mock_get_llm.call_args.kwargs
    assert kwargs["reasoning_effort"] == "high"
    assert kwargs.get("temperature") is None
