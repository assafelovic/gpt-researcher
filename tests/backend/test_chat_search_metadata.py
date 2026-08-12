from types import SimpleNamespace

import pytest

from backend.chat import chat as chat_module


@pytest.mark.asyncio
async def test_tool_search_reuses_metadata_without_second_api_call(monkeypatch):
    calls = []

    class FakeTavilyClient:
        def search(self, **kwargs):
            calls.append(kwargs)
            return {
                "results": [
                    {
                        "title": "Current result",
                        "url": "https://example.com/current",
                        "content": "Current information",
                    }
                ]
            }

    async def fake_chat_completion_with_tools(**kwargs):
        result = kwargs["tools"][0].invoke({"query": "latest update"})
        assert "Current result" in result
        return "answer", [
            {
                "tool": "search_tool",
                "args": {"query": "latest update"},
                "call_id": "call-1",
            }
        ]

    agent = chat_module.ChatAgentWithMemory.__new__(
        chat_module.ChatAgentWithMemory
    )
    agent.tavily_client = FakeTavilyClient()
    agent.search_metadata = None
    agent.config = SimpleNamespace(
        smart_llm_model="model",
        smart_llm_provider="provider",
        llm_kwargs={},
    )

    monkeypatch.setattr(
        chat_module,
        "create_chat_completion_with_tools",
        fake_chat_completion_with_tools,
    )

    response, metadata = await agent.process_chat_completion([])

    assert response == "answer"
    assert calls == [{"query": "latest update", "max_results": 5}]
    assert metadata == [
        {
            "tool": "quick_search",
            "query": "latest update",
            "search_metadata": {
                "query": "latest update",
                "sources": [
                    {
                        "title": "Current result",
                        "url": "https://example.com/current",
                        "content": "Current information",
                    }
                ],
            },
        }
    ]


def test_unavailable_search_records_error_metadata():
    agent = chat_module.ChatAgentWithMemory.__new__(
        chat_module.ChatAgentWithMemory
    )
    agent.tavily_client = None
    agent.search_metadata = None

    result = agent.quick_search("latest update")

    assert result["results"] == []
    assert agent.search_metadata_by_query["latest update"] == {
        "query": "latest update",
        "sources": [],
        "error": "Web search is disabled - TAVILY_API_KEY not configured",
    }
