"""JevContextCompressor: ranking, thresholds, API handling and fallback."""

import asyncio
import contextlib
import json
from types import SimpleNamespace

import httpx
import pytest

from gpt_researcher.context import jev_filter
from gpt_researcher.context.jev_filter import JevClient, JevContextCompressor, JevError


def _page(url, text):
    return {"url": url, "title": url, "raw_content": text}


def _long(word, n=40):
    return (f"{word} " * 120 + "\n\n") * n  # ~24k chars, well past the 8k shortcut


class FakeClient(JevClient):
    """Scores a chunk by the first word that appears in ``scores``."""

    def __init__(self, scores):
        self.api_key, self.model, self.input_tokens = "test", "jev-latest", 0
        self.scores, self.calls = scores, 0

    def session(self):
        return contextlib.nullcontext()

    async def score_relevance(self, client, query, passage):
        self.calls += 1
        self.input_tokens += 100
        return next((v for k, v in self.scores.items() if k in passage), 0.0)


def _run(coro):
    return asyncio.run(coro)


def test_keeps_best_scoring_chunks_above_threshold():
    pages = [_page("a", _long("filler")), _page("b", _long("answer")), _page("c", _long("background"))]
    client = FakeClient({"answer": 3.0, "background": 2.0, "filler": 0.4})
    context = _run(JevContextCompressor(pages, min_score=1.5, client=client).async_get_context("q", max_results=10))
    sources = [line for line in context.splitlines() if line.startswith("Source: ")]
    assert len(sources) == 10
    assert set(sources) == {"Source: b"}, "the directly answering page fills the budget first"
    assert "filler" not in context


def test_threshold_can_leave_context_empty():
    client = FakeClient({"filler": 0.2})
    context = _run(JevContextCompressor([_page("a", _long("filler"))], min_score=1.5, client=client)
                   .async_get_context("q", max_results=10))
    assert context == ""


def test_small_input_skips_the_api():
    client = FakeClient({})
    context = _run(JevContextCompressor([_page("a", "short page")], client=client).async_get_context("q"))
    assert client.calls == 0 and "short page" in context


def test_cost_is_reported_from_input_tokens():
    client = FakeClient({"answer": 3.0})
    costs = []
    _run(JevContextCompressor([_page("a", _long("answer"))], client=client)
         .async_get_context("q", cost_callback=costs.append))
    assert costs == [pytest.approx(client.calls * 100 / 1e6 * jev_filter.JEV_INPUT_PRICE_PER_MTOK)]


def _transport(responses):
    """Serve the given (status, body) pairs in order and record requests."""
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        status, body = responses[min(len(seen) - 1, len(responses) - 1)]
        return httpx.Response(status, json=body)

    return httpx.MockTransport(handler), seen


OK = {"answers": {"usefulness": {"type": "score", "score": 2.5}}, "usage": {"input_tokens": 42}}


def _score_with(transport, monkeypatch):
    real_sleep = asyncio.sleep
    monkeypatch.setattr(jev_filter.asyncio, "sleep", lambda s: real_sleep(0))
    client = JevClient(api_key="k")

    async def go():
        async with httpx.AsyncClient(transport=transport) as http:
            return await client.score_relevance(http, "what is x?", "x is y")

    return client, _run(go())


def test_request_shape_and_success(monkeypatch):
    transport, seen = _transport([(200, OK)])
    client, score = _score_with(transport, monkeypatch)
    assert score == 2.5 and client.input_tokens == 42
    question = seen[0]["questions"]["usefulness"]
    assert seen[0]["state"] == "x is y" and question["type"] == "score"
    assert "what is x?" in question["instructions"] and len(question["criteria"]) == 4


def test_retries_rate_limits(monkeypatch):
    transport, seen = _transport([(429, {}), (529, {}), (200, OK)])
    _, score = _score_with(transport, monkeypatch)
    assert score == 2.5 and len(seen) == 3


def test_auth_errors_are_not_retried(monkeypatch):
    transport, seen = _transport([(401, {"detail": "bad key"})])
    with pytest.raises(JevError):
        _score_with(transport, monkeypatch)
    assert len(seen) == 1


def test_malformed_response_is_a_jev_error(monkeypatch):
    transport, _ = _transport([(200, {"answers": {}})])
    with pytest.raises(JevError):
        _score_with(transport, monkeypatch)


def test_missing_key_is_a_jev_error(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    with pytest.raises(JevError):
        JevClient()


def test_context_manager_falls_back_to_embeddings_without_a_key(monkeypatch):
    from gpt_researcher.skills import context_manager as cm

    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    used = []

    class FakeCompressor:
        def __init__(self, **kwargs):
            used.append("embeddings")

        async def async_get_context(self, **kwargs):
            return "embedded context"

    monkeypatch.setattr(cm, "ContextCompressor", FakeCompressor)
    researcher = SimpleNamespace(
        verbose=False, websocket=None, kwargs={}, prompt_family=None, add_costs=lambda c: None,
        cfg=SimpleNamespace(context_filter="jev", similarity_threshold=0.42),
        memory=SimpleNamespace(get_embeddings=lambda: None),
    )
    result = _run(cm.ContextManager(researcher).get_similar_content_by_query("q", [_page("a", _long("x"))]))
    assert result == "embedded context" and used == ["embeddings"]


@pytest.mark.parametrize("setting,key,expected", [
    ("auto", "k", "jev"),
    ("auto", None, "embeddings"),
    (None, "k", "jev"),
    ("JEV", None, "jev"),
    ("embeddings", "k", "embeddings"),
    ("none", None, "none"),
    ("bogus", None, "embeddings"),
])
def test_resolve_context_filter(monkeypatch, setting, key, expected):
    if key:
        monkeypatch.setenv("TYPESAFE_API_KEY", key)
    else:
        monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    assert jev_filter.resolve_context_filter(setting) == expected


def test_none_filter_passes_every_page_without_embeddings():
    from gpt_researcher.prompts import PromptFamily
    from gpt_researcher.skills import context_manager as cm

    def no_embeddings():
        raise AssertionError("the none filter must not build embeddings")

    researcher = SimpleNamespace(
        verbose=False, websocket=None, kwargs={}, prompt_family=PromptFamily, add_costs=lambda c: None,
        cfg=SimpleNamespace(context_filter="none"), memory=SimpleNamespace(get_embeddings=no_embeddings),
    )
    pages = [_page("a", "alpha " * 3000), _page("b", "beta " * 3000)]
    context = _run(cm.ContextManager(researcher).get_similar_content_by_query("q", pages))
    assert "Source: a" in context and "Source: b" in context
    assert context.count("alpha") == 3000


def test_embeddings_are_built_only_when_used(monkeypatch):
    from gpt_researcher import agent

    built = []

    class CountingMemory:
        def __init__(self, *args, **kwargs):
            built.append(args)

    monkeypatch.setattr(agent, "Memory", CountingMemory)
    researcher = agent.GPTResearcher(query="q")
    assert built == [], "constructing a researcher must not build an embedding model"
    first = researcher.memory
    assert researcher.memory is first and len(built) == 1
