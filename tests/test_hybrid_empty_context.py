"""Hybrid research must not join an empty pass's [] into the report context."""

from types import SimpleNamespace

import pytest

from gpt_researcher.prompts import Granite33PromptFamily, PromptFamily
from gpt_researcher.skills import researcher as researcher_module
from gpt_researcher.skills.researcher import ResearchConductor


class _Documents:
    def __init__(self, *args, **kwargs):
        pass

    async def load(self):
        return [{"raw_content": "local text", "url": "local.txt"}]


def _conductor(monkeypatch, prompt_family, docs_context, web_context):
    monkeypatch.setattr(researcher_module, "DocumentLoader", _Documents)
    researcher = SimpleNamespace(
        query="q",
        verbose=False,
        websocket=None,
        agent="agent",
        role="role",
        source_urls=None,
        document_urls=None,
        complement_source_urls=False,
        report_source="hybrid",
        cfg=SimpleNamespace(doc_path="docs", curate_sources=False),
        vector_store=None,
        prompt_family=prompt_family,
        retrievers=[],
        query_domains=[],
        headers={},
        parent_query="",
        context=None,
        get_costs=lambda: 0,
    )
    conductor = ResearchConductor(researcher)

    async def search(query, scraped_data=None, query_domains=None):
        return docs_context if scraped_data else web_context

    conductor._get_context_by_web_search = search
    return conductor


@pytest.mark.asyncio
async def test_empty_local_pass_is_not_rendered_as_a_list(monkeypatch):
    conductor = _conductor(monkeypatch, PromptFamily, [], "web text")

    context = await conductor.conduct_research()

    assert "[]" not in context
    assert "web text" in context


@pytest.mark.asyncio
async def test_empty_pass_does_not_crash_granite_family(monkeypatch):
    conductor = _conductor(monkeypatch, Granite33PromptFamily, [], "web text")

    context = await conductor.conduct_research()

    assert "web text" in context


@pytest.mark.asyncio
async def test_two_empty_passes_leave_the_context_empty(monkeypatch):
    conductor = _conductor(monkeypatch, PromptFamily, [], [])

    assert not await conductor.conduct_research()
