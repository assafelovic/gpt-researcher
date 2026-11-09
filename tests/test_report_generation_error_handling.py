from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import gpt_researcher.actions.report_generation as report_generation
from gpt_researcher.utils.enum import Tone


def _cfg():
    return SimpleNamespace(
        smart_llm_model="test-model",
        smart_llm_provider="test-provider",
        llm_kwargs={},
        report_format="markdown",
        total_words=100,
        language="en",
        stream_output=False,
        smart_token_limit=4000,
    )


async def _generate(monkeypatch, side_effect):
    completion = AsyncMock(side_effect=side_effect)
    logger = MagicMock()
    monkeypatch.setattr(report_generation, "create_chat_completion", completion)
    monkeypatch.setattr(report_generation, "logger", logger)
    report = await report_generation.generate_report(
        query="What is solar power?",
        context="Solar panels turn sunlight into electricity.",
        agent_role_prompt="You are a research assistant.",
        report_type="research_report",
        tone=Tone.Objective,
        report_source="web",
        websocket=None,
        cfg=_cfg(),
    )
    return report, completion, logger


@pytest.mark.asyncio
async def test_generate_report_raises_when_all_attempts_fail(monkeypatch):
    with pytest.raises(RuntimeError, match="LLM connection refused"):
        await _generate(monkeypatch, RuntimeError("LLM connection refused"))

    assert report_generation.create_chat_completion.call_count == 2
    report_generation.logger.error.assert_called_with(
        "Error in generate_report: LLM connection refused"
    )


@pytest.mark.asyncio
async def test_generate_report_succeeds_on_fallback(monkeypatch):
    # First attempt fails (e.g. system role rejection), second attempt succeeds
    report, completion, logger = await _generate(
        monkeypatch, [ValueError("System role not supported"), "Report from fallback"]
    )

    assert report == "Report from fallback"
    assert completion.call_count == 2
    logger.error.assert_not_called()


@pytest.mark.asyncio
async def test_generate_report_succeeds_on_first_attempt(monkeypatch):
    report, completion, logger = await _generate(monkeypatch, ["Report from first attempt"])

    assert report == "Report from first attempt"
    assert completion.call_count == 1
    logger.error.assert_not_called()
