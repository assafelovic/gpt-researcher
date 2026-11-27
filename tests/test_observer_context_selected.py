"""The ``context_selected`` research observer event.

Offline: keyword and none need nothing, Jev runs against a stub client and
embeddings against a hashing model. Checks that the event says which filter
really ran, where each chosen chunk sits in its page, carries no page text,
and never changes the context or breaks research.
"""

import asyncio
import contextlib
import json
from types import SimpleNamespace

import pytest
from langchain_core.embeddings import Embeddings

from gpt_researcher.context import compression, jev_filter
from gpt_researcher.context.retriever import _MAX_CONTENT_CHARS
from gpt_researcher.context.select import select_context
from gpt_researcher.prompts import PromptFamily
from gpt_researcher.skills import context_manager
from gpt_researcher.skills.context_manager import ContextManager

QUERY = "solid-state battery cost per kWh"
ANSWER = "Solid-state batteries cost about $400 per kWh in 2026, roughly three times lithium-ion cells. "
SECRET = "zzsecretbodyword"  # appears only in page bodies, never in a payload


def _filler(tag, n=12):
    return "".join(
        f"{SECRET} {tag} paragraph {i}: the committee met on Tuesday to discuss agenda item {i}. " * 6 + "\n\n"
        for i in range(n)
    )


PAGES = [
    {"url": "https://a.test", "title": "A", "raw_content": _filler("a")},
    {"url": "https://b.test", "title": "B", "raw_content": _filler("b", 4) + ANSWER * 6 + "\n\n" + _filler("b2", 4)},
    {"url": "https://c.test", "title": "C", "raw_content": _filler("c")},
]
SMALL_PAGES = [
    {"url": "https://s1.test", "title": "S1", "raw_content": f"{SECRET} short page one."},
    {"url": "https://s2.test", "title": "S2", "raw_content": ANSWER},
]


class HashingEmbeddings(Embeddings):
    """Deterministic hashed bag-of-words vectors, no model, key or network."""

    def _vec(self, text):
        vec = [0.0] * 64
        for token in text.lower().split():
            vec[sum(map(ord, token)) % 64] += 1.0
        return vec

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


class StubJevClient(jev_filter.JevClient):
    """Scores chunks mentioning the answer highly, or raises like a dead API."""

    def __init__(self, fail=False):
        self.api_key, self.model, self.input_tokens, self.fail = "test", "jev-latest", 0, fail

    def session(self):
        return contextlib.nullcontext()

    async def score_relevance(self, client, query, passage):
        if self.fail:
            raise jev_filter.JevError("HTTP 503 from stub")
        return 3.0 if "$400" in passage else 0.5


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("COMPRESSION_THRESHOLD", raising=False)
    # The real estimate downloads a tiktoken encoding.
    monkeypatch.setattr(compression, "estimate_embedding_cost", lambda **kwargs: 0.0)


def _stub_jev(monkeypatch, fail=False):
    monkeypatch.setattr(jev_filter, "JevClient", lambda *a, **k: StubJevClient(fail=fail))


def _researcher(context_filter, observer=None):
    return SimpleNamespace(
        verbose=False,
        websocket=None,
        cfg=SimpleNamespace(context_filter=context_filter, similarity_threshold=0.1),
        prompt_family=PromptFamily,
        add_costs=lambda cost: None,
        memory=SimpleNamespace(get_embeddings=HashingEmbeddings),
        research_observer=observer,
    )


def _research(context_filter, pages, observer=None):
    """Context from ContextManager, and the events the observer saw."""
    events = []

    def record(event, **fields):
        events.append((event, fields))

    manager = ContextManager(_researcher(context_filter, observer or record))
    context = asyncio.run(manager.get_similar_content_by_query(QUERY, pages))
    return context, [fields for event, fields in events if event == "context_selected"]


def _plain(context_filter, pages):
    """Context from select_context with no observer, exactly as before this event existed."""
    researcher = _researcher(context_filter)
    return asyncio.run(select_context(
        QUERY, pages, researcher.cfg, max_results=10, prompt_family=PromptFamily,
        cost_callback=researcher.add_costs, embeddings=researcher.memory.get_embeddings,
    ))


def _check_offsets(event, pages, context):
    capped = {p["url"]: p["raw_content"][:_MAX_CONTENT_CHARS] for p in pages}
    assert [s["rank"] for s in event["selected"]] == list(range(1, len(event["selected"]) + 1))
    for s in event["selected"]:
        assert s["start"] is not None
        chunk = capped[s["url"]][s["start"]:s["start"] + s["length"]]
        assert len(chunk) == s["length"]
        assert f"Content: {chunk}\n" in context


def _check_no_text(event):
    assert SECRET not in json.dumps(event)
    assert set(event) == {"query", "filter", "filter_used", "fallback_reason", "candidate_pages",
                          "candidate_chunks", "context_chars", "selected"}
    for s in event["selected"]:
        assert set(s) == {"url", "rank", "start", "length", "score"}


def test_keyword_reports_ranked_chunks_with_offsets_and_scores():
    context, [event] = _research("keyword", PAGES)

    assert event["query"] == QUERY
    assert (event["filter"], event["filter_used"], event["fallback_reason"]) == ("keyword", "keyword", None)
    assert event["candidate_pages"] == 3
    assert event["candidate_chunks"] > len(event["selected"]) > 0
    assert event["context_chars"] == len(context)
    assert event["selected"][0]["url"] == "https://b.test"
    scores = [s["score"] for s in event["selected"]]
    assert all(isinstance(s, float) for s in scores) and scores == sorted(scores, reverse=True)
    _check_offsets(event, PAGES, context)
    _check_no_text(event)


def test_none_reports_every_page_capped_and_unscored():
    long_page = {"url": "https://long.test", "title": "L", "raw_content": "x" * (_MAX_CONTENT_CHARS + 500)}
    pages = PAGES + [long_page]
    context, [event] = _research("none", pages)

    assert (event["filter"], event["filter_used"], event["candidate_chunks"]) == ("none", "none", None)
    assert [s["url"] for s in event["selected"]] == [p["url"] for p in pages]
    assert all(s["start"] == 0 and s["score"] is None for s in event["selected"])
    assert event["selected"][-1]["length"] == _MAX_CONTENT_CHARS
    _check_offsets(event, pages, context)
    _check_no_text(event)


@pytest.mark.parametrize("context_filter", ["keyword", "jev", "embeddings", None])
def test_small_input_shortcut_is_reported(context_filter):
    context, [event] = _research(context_filter, SMALL_PAGES)

    assert event["filter"] == (context_filter or "auto")
    assert event["filter_used"] == "shortcut"
    assert event["fallback_reason"] is None
    assert [(s["url"], s["start"], s["score"]) for s in event["selected"]] == [
        ("https://s1.test", 0, None), ("https://s2.test", 0, None)]
    _check_offsets(event, SMALL_PAGES, context)
    _check_no_text(event)


@pytest.mark.parametrize("stubbed", [False, True], ids=["no-key", "client-raises"])
def test_jev_failure_reports_keyword_fallback(monkeypatch, stubbed):
    if stubbed:
        monkeypatch.setenv("TYPESAFE_API_KEY", "test")
        _stub_jev(monkeypatch, fail=True)
    context, [event] = _research("jev", PAGES)

    assert (event["filter"], event["filter_used"], event["fallback_reason"]) == ("jev", "keyword", "JevError")
    assert context == _plain("keyword", PAGES)
    _check_offsets(event, PAGES, context)


def test_jev_success_reports_jev_scores(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test")
    _stub_jev(monkeypatch)
    context, [event] = _research("auto", PAGES)

    assert (event["filter"], event["filter_used"], event["fallback_reason"]) == ("auto", "jev", None)
    assert event["selected"] and all(s["score"] == 3.0 and s["url"] == "https://b.test" for s in event["selected"])
    _check_offsets(event, PAGES, context)
    _check_no_text(event)


def test_embeddings_reports_similarity_scores():
    context, [event] = _research("embeddings", PAGES)

    assert (event["filter_used"], event["fallback_reason"], event["candidate_chunks"]) == ("embeddings", None, None)
    assert event["selected"] and all(isinstance(s["score"], float) for s in event["selected"])
    _check_offsets(event, PAGES, context)
    _check_no_text(event)


@pytest.mark.parametrize("context_filter,pages,jev", [
    ("keyword", PAGES, None), ("none", PAGES, None), ("keyword", SMALL_PAGES, None),
    ("embeddings", PAGES, None), ("jev", PAGES, "ok"), ("jev", PAGES, "fail"), ("jev", PAGES, None),
])
def test_context_is_byte_identical_with_and_without_observer(monkeypatch, context_filter, pages, jev):
    if jev:
        monkeypatch.setenv("TYPESAFE_API_KEY", "test")
        _stub_jev(monkeypatch, fail=jev == "fail")
    observed, events = _research(context_filter, pages)
    assert len(events) == 1
    assert observed == _plain(context_filter, pages)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_observer_failure_does_not_break_research(asynchronous):
    if asynchronous:
        async def broken(event, **fields):
            raise RuntimeError("telemetry down")
    else:
        def broken(event, **fields):
            raise RuntimeError("telemetry down")

    context, _ = _research("keyword", PAGES, observer=broken)
    assert context == _plain("keyword", PAGES)


def test_failing_selection_callback_does_not_change_context():
    def broken(details):
        raise RuntimeError("boom")

    cfg = SimpleNamespace(context_filter="keyword")
    context = asyncio.run(select_context(QUERY, PAGES, cfg, on_selected=broken))
    assert context == _plain("keyword", PAGES)


def test_no_observer_means_no_selection_callback(monkeypatch):
    seen = {}

    async def fake_select_context(*args, **kwargs):
        seen.update(kwargs)
        return "ctx"

    monkeypatch.setattr(context_manager, "select_context", fake_select_context)
    researcher = _researcher("keyword")
    researcher.research_observer = None
    assert asyncio.run(ContextManager(researcher).get_similar_content_by_query(QUERY, PAGES)) == "ctx"
    assert seen["on_selected"] is None
