"""Chat citations must describe the searches actually supplied to the model."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from backend.chat.chat import ChatAgentWithMemory
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider


class ScriptedModel:
    """Only the provider boundary is faked; real tools execute in between calls."""

    def __init__(self, queries):
        self.calls = []
        self.responses = [
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "search_tool", "args": {"query": query}, "id": f"call-{i}"}
                    for i, query in enumerate(queries)
                ],
            ),
            AIMessage(content="Answer grounded in the search results."),
        ] if queries else [AIMessage(content="Answer from the report.")]

    def bind_tools(self, tools):
        return self

    async def ainvoke(self, messages):
        self.calls.append(list(messages))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture
def agent(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    agent = ChatAgentWithMemory(report="")
    calls = []

    def search(*, query, max_results):
        assert max_results == 5
        calls.append(query)
        if query == "fail":
            raise RuntimeError("search unavailable")
        return {"results": [{
            "title": f"Source for {query}",
            "url": f"https://example.com/result-{len(calls)}",
            "content": "Evidence " * 60,
        }]}

    agent.tavily_client = MagicMock()
    agent.tavily_client.search.side_effect = search
    return agent


def install_model(monkeypatch, queries):
    model = ScriptedModel(queries)
    monkeypatch.setattr(
        GenericLLMProvider, "from_provider",
        lambda *_args, **_kwargs: SimpleNamespace(llm=model),
    )
    return model


@pytest.mark.asyncio
@pytest.mark.parametrize("queries", [
    ["first"], ["first", "second"], ["same", "same"],
    ["first", "fail"], ["fail"], ["fail", "second"],
])
async def test_each_tool_call_searches_once_and_keeps_its_own_sources(agent, monkeypatch, queries):
    model = install_model(monkeypatch, queries)

    response, metadata = await agent.chat([{"role": "user", "content": "Find current evidence."}])

    assert response == "Answer grounded in the search results."
    assert agent.tavily_client.search.call_count == len(queries)
    assert len(metadata) == len(queries)
    evidence = [message for message in model.calls[1] if isinstance(message, ToolMessage)]
    assert len(evidence) == len(queries)
    for index, (query, entry, tool_message) in enumerate(zip(queries, metadata, evidence), start=1):
        assert entry["tool"] == "quick_search"
        assert entry["query"] == query
        assert entry["search_metadata"]["query"] == query
        if query == "fail":
            assert entry["search_metadata"]["sources"] == []
            assert entry["search_metadata"]["error"] == "search unavailable"
        else:
            source = entry["search_metadata"]["sources"][0]
            assert source["url"] == f"https://example.com/result-{index}"
            assert source["url"] in tool_message.content
            assert source["title"] in tool_message.content
            assert source["content"] == ("Evidence " * 60)[:200] + "..."


def test_failed_search_replaces_previous_metadata(agent):
    agent.quick_search("first")

    result = agent.quick_search("fail")

    assert result == {"error": "search unavailable", "results": []}
    assert agent.search_metadata == {
        "query": "fail", "sources": [], "error": "search unavailable",
    }


@pytest.mark.asyncio
async def test_disabled_search_has_current_error_and_no_previous_sources(agent, monkeypatch):
    agent.quick_search("first")
    agent.tavily_client = None
    install_model(monkeypatch, ["disabled"])

    _, metadata = await agent.process_chat_completion([])

    assert len(metadata) == 1
    assert metadata[0]["search_metadata"] == {
        "query": "disabled", "sources": [],
        "error": "Web search is disabled - TAVILY_API_KEY not configured",
    }


@pytest.mark.asyncio
async def test_chat_without_search_does_not_reuse_previous_turn_metadata(agent, monkeypatch):
    install_model(monkeypatch, ["first"])
    _, previous = await agent.process_chat_completion([])
    calls_before = agent.tavily_client.search.call_count
    install_model(monkeypatch, [])

    response, current = await agent.process_chat_completion([])

    assert response == "Answer from the report."
    assert current == []
    assert previous[0]["search_metadata"]["query"] == "first"
    assert agent.tavily_client.search.call_count == calls_before


@pytest.mark.asyncio
async def test_plain_completion_fallback_does_not_publish_unused_sources(agent, monkeypatch):
    model = install_model(monkeypatch, ["first"])
    model.responses[1] = RuntimeError("final model call failed")
    fallback = AsyncMock(return_value="Answer without search evidence.")
    monkeypatch.setattr("gpt_researcher.utils.tools.create_chat_completion", fallback)

    response, metadata = await agent.process_chat_completion([])

    assert response == "Answer without search evidence."
    assert metadata == []
    assert agent.tavily_client.search.call_count == 1
    fallback.assert_awaited_once()


@pytest.mark.asyncio
async def test_overlapping_completions_keep_sources_separate(agent, monkeypatch):
    first_ready, second_ready = asyncio.Event(), asyncio.Event()

    class InterleavedModel(ScriptedModel):
        def __init__(self, query, ready, other_ready):
            super().__init__([query])
            self.ready, self.other_ready = ready, other_ready

        async def ainvoke(self, messages):
            if self.calls:
                self.ready.set()
                await asyncio.wait_for(self.other_ready.wait(), timeout=5)
            return await super().ainvoke(messages)

    models = [
        InterleavedModel("first", first_ready, second_ready),
        InterleavedModel("second", second_ready, first_ready),
    ]
    providers = iter(SimpleNamespace(llm=model) for model in models)
    monkeypatch.setattr(GenericLLMProvider, "from_provider", lambda *_a, **_kw: next(providers))

    completions = await asyncio.gather(
        agent.process_chat_completion([]), agent.process_chat_completion([]),
    )

    assert agent.tavily_client.search.call_count == 2
    for query, model, (_, metadata) in zip(["first", "second"], models, completions):
        assert len(metadata) == 1
        search_metadata = metadata[0]["search_metadata"]
        assert search_metadata["query"] == query
        source = search_metadata["sources"][0]
        assert source["title"] == f"Source for {query}"
        evidence = next(message for message in model.calls[1] if isinstance(message, ToolMessage))
        assert source["url"] in evidence.content
