"""Report chat selects report context with the same filter as research."""

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.chat import chat as chat_module
from backend.chat.chat import ChatAgentWithMemory

REPORT = (
    "## Costs\n" + "Solid-state batteries cost about $400 per kWh in 2026. " * 40 + "\n\n"
    "## History\n" + "The committee met on Tuesday and discussed the agenda. " * 200
)


def _agent(context_filter="keyword", retriever=None, report=REPORT):
    agent = ChatAgentWithMemory.__new__(ChatAgentWithMemory)
    agent.report = report
    agent.config = SimpleNamespace(context_filter=context_filter)
    agent.retriever = retriever
    return agent


def _context(agent, message="How much do solid-state batteries cost per kWh?"):
    return asyncio.run(agent._retrieve_context(message))


def test_no_embeddings_are_needed(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    assert not hasattr(chat_module, "Memory") and not hasattr(chat_module, "InMemoryVectorStore")
    context = _context(_agent("auto"))
    assert "$400 per kWh" in context
    assert context.count("committee met") < REPORT.count("committee met") / 4


def test_none_filter_uses_the_full_report():
    context = _context(_agent("none"))
    assert context.count("committee met") == REPORT.count("committee met")


def test_short_report_is_used_whole():
    assert "tiny report" in _context(_agent(report="A tiny report."))


def test_injected_vector_store_retriever_is_used_first():
    retriever = MagicMock()
    retriever.invoke.return_value = [SimpleNamespace(page_content="chunk-1"), SimpleNamespace(page_content="chunk-2")]
    assert _context(_agent(retriever=retriever)) == "chunk-1\n\nchunk-2"


def test_failing_injected_retriever_falls_back_to_the_context_filter():
    retriever = MagicMock()
    retriever.invoke.side_effect = RuntimeError("store down")
    assert "$400 per kWh" in _context(_agent(retriever=retriever))


def test_empty_message_or_report():
    assert _context(_agent(), message="") == REPORT
    assert _context(_agent(report="")) == ""


def test_constructor_wraps_an_injected_vector_store(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    store = MagicMock()
    store.as_retriever.return_value = "retriever-ok"
    agent = ChatAgentWithMemory(report=REPORT, vector_store=store)
    store.as_retriever.assert_called_once_with(search_kwargs={"k": 4})
    assert agent.retriever == "retriever-ok"
