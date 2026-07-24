"""Empty provided source_urls context must emit answering_from_memory (#1978)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from gpt_researcher.skills.researcher import ResearchConductor


def _researcher(*, verbose: bool, complement: bool = False):
    return SimpleNamespace(
        query="q",
        parent_query=None,
        agent="agent",
        role="role",
        verbose=verbose,
        websocket=None,
        headers={},
        source_urls=["https://example.com"],
        complement_source_urls=complement,
        report_source="web",
        query_domains=[],
        retrievers=[],
        vector_store=None,
        cfg=SimpleNamespace(doc_path=".", curate_sources=False),
        prompt_family=None,
        add_costs=lambda *_a, **_k: None,
        get_costs=lambda: 0,
        context=None,
        research_sources=[],
        research_images=[],
        source_curator=None,
    )


@pytest.mark.asyncio
async def test_empty_string_context_emits_notification():
    researcher = _researcher(verbose=True)
    conductor = ResearchConductor(researcher)
    conductor.json_handler = None
    conductor._get_context_by_urls = AsyncMock(return_value="")

    with patch(
        "gpt_researcher.skills.researcher.stream_output", new_callable=AsyncMock
    ) as stream:
        await conductor.conduct_research()

    types = [c.args[1] for c in stream.call_args_list if len(c.args) > 1]
    assert "answering_from_memory" in types


@pytest.mark.asyncio
async def test_empty_list_context_emits_notification():
    researcher = _researcher(verbose=True)
    conductor = ResearchConductor(researcher)
    conductor.json_handler = None
    conductor._get_context_by_urls = AsyncMock(return_value=[])

    with patch(
        "gpt_researcher.skills.researcher.stream_output", new_callable=AsyncMock
    ) as stream:
        await conductor.conduct_research()

    types = [c.args[1] for c in stream.call_args_list if len(c.args) > 1]
    assert "answering_from_memory" in types


@pytest.mark.asyncio
async def test_nonempty_context_skips_notification():
    researcher = _researcher(verbose=True)
    conductor = ResearchConductor(researcher)
    conductor.json_handler = None
    conductor._get_context_by_urls = AsyncMock(return_value="useful context")

    with patch(
        "gpt_researcher.skills.researcher.stream_output", new_callable=AsyncMock
    ) as stream:
        await conductor.conduct_research()

    types = [c.args[1] for c in stream.call_args_list if len(c.args) > 1]
    assert "answering_from_memory" not in types


@pytest.mark.asyncio
async def test_empty_context_silent_when_verbose_false():
    researcher = _researcher(verbose=False)
    conductor = ResearchConductor(researcher)
    conductor.json_handler = None
    conductor._get_context_by_urls = AsyncMock(return_value="")

    with patch(
        "gpt_researcher.skills.researcher.stream_output", new_callable=AsyncMock
    ) as stream:
        await conductor.conduct_research()

    types = [c.args[1] for c in stream.call_args_list if len(c.args) > 1]
    assert "answering_from_memory" not in types
