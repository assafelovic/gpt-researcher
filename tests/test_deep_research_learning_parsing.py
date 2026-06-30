"""Regression test for learning/citation parsing in DeepResearchSkill.

``process_research_results`` parses LLM output lines shaped like
``Learning [https://example.com/page]: <insight>``. The old implementation
used ``line.split(':', 1)[1]`` to grab the insight, which split on the colon
inside the URL scheme (``https:``) and produced a mangled learning such as
``//example.com/page]: <insight>``. The citation URL was captured correctly,
but the learning text (and therefore the citation key) was corrupted.
"""

import sys
import types
from unittest.mock import patch

import pytest


def _make_skill():
    from gpt_researcher.skills.deep_research import DeepResearchSkill

    cfg = types.SimpleNamespace(
        deep_research_breadth=4,
        deep_research_depth=2,
        deep_research_concurrency=2,
        config_path=None,
        strategic_llm_provider="openai",
        strategic_llm_model="gpt-4o",
        reasoning_effort="medium",
    )
    researcher = types.SimpleNamespace(
        cfg=cfg,
        websocket=None,
        tone=None,
        headers={},
        visited_urls=set(),
    )
    return DeepResearchSkill(researcher)


@pytest.mark.asyncio
async def test_learning_with_url_is_not_mangled_by_scheme_colon():
    skill = _make_skill()
    response = (
        "Learning [https://example.com/page]: The sky appears blue due to "
        "Rayleigh scattering\n"
        "Question: What causes red sunsets?"
    )

    with patch(
        "gpt_researcher.skills.deep_research.create_chat_completion",
        return_value=response,
    ):
        result = await skill.process_research_results("why is the sky blue", "ctx")

    expected_learning = (
        "The sky appears blue due to Rayleigh scattering"
    )
    assert result["learnings"] == [expected_learning]
    # The insight must NOT leak the URL remnant from the scheme colon split.
    assert "//example.com" not in result["learnings"][0]
    assert result["citations"] == {
        expected_learning: "https://example.com/page"
    }
    assert result["followUpQuestions"] == ["What causes red sunsets?"]
