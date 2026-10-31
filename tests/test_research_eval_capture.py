"""
End-to-end tests for evals/research_eval/capture.py.

The real GPTResearcher / ResearchConductor / DeepResearchSkill code runs; only
the network edges (search, scraping, LLM calls) are replaced with fakes. That
way the tests check the span tree the hooks build from the library's actual
call graph, including concurrency via asyncio.gather.
"""

import asyncio
import json
import re

import pytest

from evals.research_eval.archive import RunArchive, build_archive
from evals.research_eval.capture import RunCapture
from evals.research_eval.tracing import Tracer


def _slug(q: str) -> str:
    return re.sub(r"\W+", "-", q.lower()).strip("-")[:40]


class FakeRetriever:
    """Two results per query; the second URL is shared by every query (overlap)."""
    requires_scraping = True

    def __init__(self, query, query_domains=None, **kw):
        self.query = query

    def search(self, max_results=5):
        return [{"href": f"https://{_slug(self.query)}.example.org/page", "body": "snippet"},
                {"href": "https://shared.example.com/common", "body": "snippet"}]


async def _fake_get_search_results(query, retriever, query_domains=None, researcher=None, max_results=None):
    return FakeRetriever(query).search()


async def _fake_browse(self, urls, *a, **k):
    return [{"url": u, "title": f"Title of {u}",
             "raw_content": f"Page {u} discusses regulation policy details and market data."}
            for u in urls]


@pytest.fixture
def fake_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.setenv("CONTEXT_FILTER", "keyword")
    from gpt_researcher.skills import researcher as researcher_mod
    from gpt_researcher.skills import deep_research as deep_mod
    from gpt_researcher.skills.browser import BrowserManager

    async def fake_choose_agent(**kw):
        return "agent", "role"

    async def fake_outline(query, **kw):
        return [f"{query} :: aspect A", f"{query} :: aspect B"]

    from gpt_researcher import agent as agent_mod
    monkeypatch.setattr(agent_mod, "choose_agent", fake_choose_agent)
    monkeypatch.setattr(researcher_mod, "choose_agent", fake_choose_agent)
    monkeypatch.setattr(researcher_mod, "plan_research_outline", fake_outline)
    monkeypatch.setattr(researcher_mod, "get_search_results", _fake_get_search_results)
    monkeypatch.setattr(deep_mod, "get_search_results", _fake_get_search_results)
    monkeypatch.setattr(BrowserManager, "browse_urls", _fake_browse)

    async def fake_completion(messages, **kw):
        user = messages[-1]["content"]
        if "unique search queries" in user:
            n = int(re.search(r"generate (\d+) unique", user).group(1))
            tag = "deeper" if "Previous research goal" in user else "top"
            return json.dumps([{"query": f"{tag} serp {i}", "researchGoal": f"{tag} goal {i}"}
                               for i in range(n)])
        if "Return ONLY a JSON object using this exact schema:\n{\"questions\"" in user:
            return json.dumps({"questions": ["clarify 1", "clarify 2"]})
        q = re.search(r"research results for the query '([^']*)'", user).group(1)
        return json.dumps({"learnings": [{"insight": f"learned about {q}", "sourceUrl": ""}],
                           "followUpQuestions": [f"follow up on {q}"]})

    monkeypatch.setattr(deep_mod, "create_chat_completion", fake_completion)


def _new_researcher(query, **kw):
    from gpt_researcher.agent import GPTResearcher
    r = GPTResearcher(query=query, verbose=False, **kw)
    r.retrievers = [FakeRetriever]
    return r


def _archive(capture, query, report=""):
    return RunArchive(build_archive(
        meta={"run_id": "r1", "question_id": "q1", "query": query, "config": {}},
        spans=capture.tracer.to_list(), chunks=capture.chunks, report_markdown=report))


async def test_default_mode_builds_plan_tree_and_restores_library(fake_env):
    from gpt_researcher.agent import GPTResearcher
    from gpt_researcher.skills.researcher import ResearchConductor
    originals = (GPTResearcher.conduct_research, ResearchConductor._process_sub_query,
                 ResearchConductor._get_new_urls)

    query = "eu crypto regulation"
    capture = RunCapture(Tracer())
    with capture:
        with capture.tracer.span("run", query=query):
            r = _new_researcher(query)
            await r.conduct_research()

    assert (GPTResearcher.conduct_research, ResearchConductor._process_sub_query,
            ResearchConductor._get_new_urls) == originals

    a = _archive(capture, query)
    by_name = {}
    for s in a.spans:
        by_name.setdefault(s["name"], []).append(s)
    run, = by_name["run"]
    research, = by_name["research"]
    plan, = by_name["plan"]
    assert research["parent_id"] == run["span_id"]
    assert plan["parent_id"] == research["span_id"]
    # Planned list is a copy: the core query appended by the library is not in it.
    assert plan["attributes"]["sub_queries"] == [f"{query} :: aspect A", f"{query} :: aspect B"]

    subs = by_name["sub_query"]
    assert sorted(s["attributes"]["query"] for s in subs) == sorted(
        [f"{query} :: aspect A", f"{query} :: aspect B", query])
    assert all(s["parent_id"] == plan["span_id"] for s in subs)
    assert [s["attributes"]["is_core_query"] for s in subs if s["attributes"]["query"] == query] == [True]

    initial, = by_name["initial_results"]
    assert initial["parent_id"] == research["span_id"]

    # H3: every search proposed the shared URL; only the first to arrive kept it.
    units = a.retrieval_units
    assert sum(u.proposed_urls.count("https://shared.example.com/common") for u in units) == 4
    assert sum(u.new_urls.count("https://shared.example.com/common") for u in units) == 1
    # H4/H6: chunks parsed from the real keyword selector's output, linked by id.
    # The core query re-proposes exactly what the initial search already took,
    # so de-duplication leaves it nothing; the planned aspects get fresh pages.
    for s in subs + [initial]:
        if s["attributes"]["query"] == query and s["name"] == "sub_query":
            assert s["attributes"]["chunk_ids"] == []
            continue
        assert s["attributes"]["chunk_ids"], s["attributes"]["query"]
        assert s["attributes"]["context_filter"] == "keyword"
    for cid in a.retrieved_chunk_ids:
        assert a.chunks[cid]["url"].startswith("https://")
    assert capture.health["subquery_errors"] == 0


async def test_concurrent_runs_do_not_share_spans(fake_env):
    capture = RunCapture(Tracer())
    with capture:
        with capture.tracer.span("run", query="both"):
            await asyncio.gather(_new_researcher("alpha topic").conduct_research(),
                                 _new_researcher("beta topic").conduct_research())
    a = _archive(capture, "both")
    for research in (s for s in a.spans if s["name"] == "research"):
        q = research["attributes"]["query"]
        for d in a.descendants(research["span_id"]):
            if "query" in d["attributes"]:
                assert d["attributes"]["query"].startswith(q), (q, d["attributes"]["query"])


async def test_deep_mode_tree(fake_env, monkeypatch):
    query = "drone delivery vendors"
    capture = RunCapture(Tracer())
    with capture:
        with capture.tracer.span("run", query=query):
            r = _new_researcher(query, report_type="deep")
            r.deep_researcher.breadth, r.deep_researcher.depth = 2, 2
            r.deep_researcher.concurrency_limit = 2
            # Nested researchers are built inside the library; give them the fake retriever too.
            from gpt_researcher import agent as agent_mod
            orig_init = agent_mod.GPTResearcher.__init__

            def init(self, *a, **k):
                orig_init(self, *a, **k)
                self.retrievers = [FakeRetriever]

            monkeypatch.setattr(agent_mod.GPTResearcher, "__init__", init)
            await r.conduct_research()

    a = _archive(capture, query)
    deep_plan = [s for s in a.spans if s["name"] == "deep_plan"]
    assert deep_plan and deep_plan[0]["attributes"]["questions"] == ["clarify 1", "clarify 2"]

    levels = [s for s in a.spans if s["name"] == "deep_level"]
    top = [l for l in levels if a.span_by_id[l["parent_id"]]["name"] == "research"
           and a.span_by_id[l["parent_id"]]["attributes"]["query"] == query]
    assert len(top) == 1
    assert [q["query"] for q in top[0]["attributes"]["serp_queries"]] == ["top serp 0", "top serp 1"]

    branches = [s for s in a.children[top[0]["span_id"]] if s["name"] == "research"]
    assert sorted(b["attributes"]["query"] for b in branches) == ["top serp 0", "top serp 1"]
    for b in branches:
        assert b["attributes"]["research_goal"].startswith("top goal")
        assert b["attributes"]["learnings"] == [f"learned about {b['attributes']['query']}"]
        # The deeper level launched from this branch's follow-ups hangs under it.
        deeper = [s for s in a.children[b["span_id"]] if s["name"] == "deep_level"]
        assert len(deeper) == 1
        assert f"Previous research goal: {b['attributes']['research_goal']}" in deeper[0]["attributes"]["query"]
        assert a.subtree_chunk_ids(b["span_id"])

    kinds = {d.kind for d in a.decompositions}
    assert {"deep_plan", "deep_level", "plan"} <= kinds


async def test_detailed_subtopics_and_health_events(fake_env):
    import logging
    from types import SimpleNamespace

    query = "vector databases"
    capture = RunCapture(Tracer())
    with capture:
        with capture.tracer.span("run", query=query):
            r = _new_researcher(query)

            async def fake_subtopics():
                return SimpleNamespace(subtopics=[SimpleNamespace(task="pricing"),
                                                  SimpleNamespace(task="features")])

            r.report_generator.get_subtopics = fake_subtopics
            await r.get_subtopics()
            sub = _new_researcher("pricing", report_type="subtopic_report", parent_query=query)
            await sub.conduct_research()
            with capture.tracer.span("sub_query", query="x"):
                logging.getLogger("research").error("Error processing sub-query x: boom")
                logging.getLogger("gpt_researcher.context.select").warning(
                    "Jev context filter unavailable (no key); using keyword ranking")

    a = _archive(capture, query)
    subtopics, = [d for d in a.decompositions if d.kind == "subtopics"]
    assert subtopics.child_queries == ["pricing", "features"]
    pricing, = [s for s in a.spans if s["name"] == "research" and s["attributes"]["query"] == "pricing"]
    assert pricing["attributes"]["parent_query"] == query
    # subtopic reports do not append their own query as an extra sub-query
    assert not any(u.is_core_query for u in a.retrieval_units if u.kind == "sub_query")
    assert capture.health["subquery_errors"] == 1
    assert capture.health["jev_fallback"] == 1
    x, = [s for s in a.spans if s["attributes"].get("query") == "x"]
    assert x["attributes"]["health_events"] == ["subquery_errors", "jev_fallback"]
    # handlers are removed on exit
    logging.getLogger("research").error("Error processing sub-query y")
    assert capture.health["subquery_errors"] == 1


async def test_captured_archive_scores_with_rule_metrics(fake_env):
    from evals.research_eval.cache import EvalCache
    from evals.research_eval.metrics import all_metrics
    from evals.research_eval.metrics.base import ScoringContext
    from evals.research_eval.scoring import score_archive

    query = "eu crypto regulation"
    capture = RunCapture(Tracer())
    with capture:
        with capture.tracer.span("run", query=query):
            await _new_researcher(query).conduct_research()
    a = _archive(capture, query, report="# R\n\nSee https://eu-crypto-regulation-aspect-a.example.org/page here.\n")
    rules = [m for m in all_metrics() if not (m.uses_llm or m.uses_embeddings)]
    rec = await score_archive(a, rules, ScoringContext(cache=EvalCache(":memory:")))
    m = rec["metrics"]
    assert m["plan_adherence"]["value"] == 1.0
    # 4 searches x 2 results. New: the initial search's two pages and one own
    # page per aspect; the core sub-query repeats the initial search entirely.
    assert m["retrieval_overlap"]["details"]["proposed"] == 8
    assert m["retrieval_overlap"]["value"] == 0.5
    assert m["source_diversity"]["details"]["retrieved"]["n"] == 4
