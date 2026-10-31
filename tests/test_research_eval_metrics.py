"""Tests for the retrieval metrics and the scoring layer of evals/research_eval.

Archives are built by hand so every expected number can be worked out from
the fixture; the judge and the embedder are offline fakes.
"""

import json
import re

import pytest

from evals.research_eval.archive import RunArchive, build_archive
from evals.research_eval.cache import EvalCache
from evals.research_eval.chunks import chunk_id
from evals.research_eval.judge import Embedder, Judge
from evals.research_eval.metrics import all_metrics
from evals.research_eval.metrics.base import ScoringContext
from evals.research_eval.metrics.retrieval import (
    CitationUtilization, DecompositionCoverage, DecompositionTreeQuality, PlanAdherence,
    QueryRelevance, RetrievalOverlap, SourceAuthority, SourceDiversity, SubqueryRedundancy)
from evals.research_eval.scoring import save_results, score_archive, scorer_version

CORE = "battery supply chain risks"

CHUNK_TEXT = {
    "cobalt": "Cobalt mining concentrated in Congo creates supply risk for battery makers in 2024.",
    "lithium": "Lithium refining capacity sits mostly in China, according to agency data.",
    "unused": "Weather forecasts for the coming weekend show rain across northern regions.",
}
URLS = {"cobalt": "https://www.reuters.com/cobalt", "lithium": "https://energy.gov/lithium",
        "unused": "https://weather-blog.com/rain"}


def _chunk(key):
    return chunk_id(URLS[key], CHUNK_TEXT[key]), {
        "url": URLS[key], "title": key, "content": CHUNK_TEXT[key], "jev_score": None}


def make_archive(report=None):
    chunks = dict(_chunk(k) for k in CHUNK_TEXT)
    cid = {k: _chunk(k)[0] for k in CHUNK_TEXT}
    spans = [
        {"span_id": "s1", "parent_id": None, "name": "run", "attributes": {"query": CORE}},
        {"span_id": "s2", "parent_id": "s1", "name": "research", "attributes": {"query": CORE}},
        {"span_id": "s3", "parent_id": "s2", "name": "plan", "attributes": {
            "query": CORE, "sub_queries": ["cobalt supply concentration",
                                           "lithium refining capacity",
                                           "lithium refining capacity worldwide",
                                           "sodium battery alternatives"]}},
        {"span_id": "s4", "parent_id": "s3", "name": "sub_query", "attributes": {
            "query": "cobalt supply concentration", "chunk_ids": [cid["cobalt"]],
            "proposed_urls": [URLS["cobalt"], "https://dup.com"], "new_urls": [URLS["cobalt"], "https://dup.com"]}},
        {"span_id": "s5", "parent_id": "s3", "name": "sub_query", "attributes": {
            "query": "lithium refining capacity", "chunk_ids": [cid["lithium"], cid["unused"]],
            "proposed_urls": [URLS["lithium"], URLS["unused"], "https://dup.com"],
            "new_urls": [URLS["lithium"], URLS["unused"]]}},
        {"span_id": "s6", "parent_id": "s3", "name": "sub_query", "attributes": {
            "query": "lithium refining capacity worldwide", "chunk_ids": [],
            "proposed_urls": ["https://dup.com"], "new_urls": []}},
        # "sodium battery alternatives" was planned but never executed.
        {"span_id": "s7", "parent_id": "s3", "name": "sub_query", "attributes": {
            "query": CORE, "is_core_query": True, "chunk_ids": [cid["cobalt"]],
            "proposed_urls": [], "new_urls": []}},
    ]
    report = report if report is not None else (
        "# Battery risks\n\n## Supply\n\n"
        "Cobalt mining is concentrated in Congo, which creates supply risk for battery makers "
        "([Reuters](https://reuters.com/cobalt)).\n\n"
        "Lithium prices moved a lot over the past year for many unrelated reasons entirely.\n\n"
        "## References\n\n- https://reuters.com/cobalt\n")
    return RunArchive(build_archive(
        meta={"run_id": "run-1", "question_id": "q1", "query": CORE, "config": {"mode": "default"}},
        spans=spans, chunks=chunks, report_markdown=report))


class FakeJudge:
    """Backend for Judge: answers each prompt type with a canned verdict."""

    def __init__(self):
        self.prompts = []

    async def __call__(self, prompt):
        self.prompts.append(prompt)
        # Generation prompts (detailed behaviour is tested in test_research_eval_generation.py).
        if "checking one paragraph of a research report" in prompt:
            cited = "(cites: [1])" in prompt
            return json.dumps({"kind": "factual",
                               "claims": [{"claim": "c", "verdict": "supported" if cited else "unsupported",
                                           "passages": ["1a"], "evidence": ""}],
                               "sentences": [{"sentence": 1, "supported": True,
                                              "citations": [{"source": 1, "alone": True}]}] if cited else []})
        if "a finished report covers" in prompt:
            return json.dumps({"points": [{"point": 1, "coverage": "full"}]})
        if "preparing a grading rubric" in prompt:
            return json.dumps({"insight": [{"criterion": "a", "weight": 1}],
                               "readability": [{"criterion": "b", "weight": 1}]})
        if "grading a research report on an absolute scale" in prompt:
            return json.dumps({"scores": [{"id": "I1", "score": 7}, {"id": "R1", "score": 8}]})
        if "whether each paragraph of a research report" in prompt:
            n = len(re.findall(r"^\d+\. ", prompt.split("Paragraphs:")[1], re.M))
            return json.dumps({"verdicts": [{"paragraph": i, "verdict": "yes"} for i in range(1, n + 1)]})
        if "screening part of a research report" in prompt:
            return json.dumps({"opinions": []})
        if "List the distinct aspects" in prompt:
            return json.dumps({"key_points": ["cobalt supply", "lithium refining", "recycling policy"]})
        if "which aspects of a research question" in prompt:
            points = re.findall(r"^(\d+)\. (.+)$", prompt.split("Key points:")[1].split("Sub-queries:")[0], re.M)
            subs = re.findall(r"^(\d+)\. (.+)$", prompt.split("Sub-queries:")[1].split("Return ONLY")[0], re.M)
            return json.dumps({"points": [
                {"point": int(i), "evidence": "",
                 "subqueries": [int(j) for j, q in subs if p.split()[0] in q]} for i, p in points]})
        if "how a research agent split a query" in prompt:
            return json.dumps({"q1": {"score": 1}, "q2": {"score": 2}, "q3": {"score": 2},
                               "q4": {"score": 1}, "q5": {"score": 2}, "total": 8})
        if "auditing one retrieval step" in prompt:
            q = re.search(r"Sub-query under review:\n(.*)\n", prompt).group(1)
            return json.dumps({"total": 8 if "cobalt" in q else 4,
                               "q4": {"evidence": "", "unique": "cobalt" in q}})
        if "used information from a source passage" in prompt:
            return json.dumps({"used": "Lithium" in prompt.split("Report sentences")[0], "evidence": ""})
        if "Rate the authority" in prompt:
            return json.dumps([{"domain": "weather-blog.com", "score": 0.2, "reason": "blog"}])
        raise AssertionError(prompt[:80])


VOCAB = ["cobalt", "lithium", "refining", "supply", "recycling", "policy", "sodium", "concentration"]


async def fake_embed(texts):
    return [[1.0 if w in t.lower() else 0.0 for w in VOCAB] + [0.01] for t in texts]


@pytest.fixture
def ctx():
    cache = EvalCache(":memory:")
    fake = FakeJudge()
    c = ScoringContext(cache=cache, judge=Judge(cache, model="judge-x", complete=fake),
                       embedder=Embedder(cache, model="emb:x", embed=fake_embed))
    c.fake = fake
    return c


async def test_decomposition_coverage_uses_judge_mapping(ctx):
    r = await DecompositionCoverage().score(make_archive(), ctx)
    assert r.details["method"] == "judge"
    covered = {p["key_point"]: p["subqueries"] for p in r.details["per_point"]}
    assert covered == {"cobalt supply": ["cobalt supply concentration"],
                       "lithium refining": ["lithium refining capacity",
                                            "lithium refining capacity worldwide"],
                       "recycling policy": []}
    assert r.value == pytest.approx(2 / 3, abs=1e-3)
    assert r.details["key_points"]["source"] == "judge"
    prompt = next(p for p in ctx.fake.prompts if "which aspects of a research question" in p)
    assert "4. sodium battery alternatives" in prompt and CORE not in prompt.split("Sub-queries:")[1]


async def test_decomposition_coverage_embedding_fallback_with_frozen_points(ctx, tmp_path):
    (tmp_path / "q1.json").write_text(json.dumps({"key_points": ["cobalt supply", "recycling policy"]}))
    ctx.key_points_dir, ctx.judge = tmp_path, None
    r = await DecompositionCoverage().score(make_archive(), ctx)
    assert r.details["method"] == "embedding_fallback"
    assert [p["covered"] for p in r.details["per_point"]] == [True, False]


async def test_decomposition_coverage_judge_failure_is_skipped(ctx):
    async def bad(prompt):
        if "List the distinct aspects" in prompt:
            return json.dumps({"key_points": ["cobalt supply"]})
        return "not json"
    ctx.judge = Judge(ctx.cache, model="judge-y", complete=bad)
    r = await DecompositionCoverage().score(make_archive(), ctx)
    assert r.value is None and r.skipped == "judge call failed"


async def test_key_points_frozen_file_wins(ctx, tmp_path):
    (tmp_path / "q1.json").write_text(json.dumps({"key_points": ["cobalt supply"]}))
    ctx.key_points_dir = tmp_path
    r = await DecompositionCoverage().score(make_archive(), ctx)
    assert r.value == 1.0 and r.details["key_points"]["source"] == "frozen"
    assert not any("List the distinct aspects" in p for p in ctx.fake.prompts)


async def test_subquery_redundancy_reads_query_relevance_q4(ctx):
    a = make_archive()
    r = await SubqueryRedundancy().score(a, ctx)
    assert r.details["method"] == "judge_q4" and r.details["steps"] == 2
    assert [x["query"] for x in r.details["not_unique"]] == ["lithium refining capacity"]
    assert r.value == 0.5 and r.higher_is_better is False
    # query_relevance reuses the same judgements: no new calls.
    before = len(ctx.fake.prompts)
    await QueryRelevance().score(a, ctx)
    assert len(ctx.fake.prompts) == before


async def test_subquery_redundancy_lexical_fallback_flags_near_duplicates():
    ctx = ScoringContext(cache=EvalCache(":memory:"))       # no judge
    r = await SubqueryRedundancy().score(make_archive(), ctx)
    assert r.details["method"] == "lexical" and r.details["pairs"] == 6
    pairs = {(d["a"], d["b"]) for d in r.details["duplicate_pairs"]}
    assert pairs == {("lithium refining capacity", "lithium refining capacity worldwide")}
    assert r.value == pytest.approx(1 / 6, abs=1e-3)
    assert r.higher_is_better is False


async def test_tree_quality_uses_judge_total(ctx):
    r = await DecompositionTreeQuality().score(make_archive(), ctx)
    assert r.value == 0.8                                   # 8 / 10
    assert r.llm["requests"] == r.llm["api_calls"] == 1 and r.llm["judge_model"] == "judge-x"
    assert r.llm["prompts"]["tree_quality"]["version"] == "2"
    prompt = next(p for p in ctx.fake.prompts if "how a research agent split a query" in p)
    assert f"Original research question (the root of the whole search tree):\n{CORE}" in prompt


async def test_plan_adherence_counts_empty_and_unexecuted(ctx):
    r = await PlanAdherence().score(make_archive(), ctx)
    assert (r.details["planned"], r.details["delivered"]) == (4, 2)
    assert {f["query"] for f in r.details["not_delivered"]} == {
        "lithium refining capacity worldwide", "sodium battery alternatives"}


async def test_source_diversity(ctx):
    r = await SourceDiversity().score(make_archive(), ctx)
    # One body citation: nothing to spread over.
    assert r.details["basis"] == "cited" and r.value == 0.0
    assert r.details["retrieved"]["domains"] == 3 and r.details["diversity_ratio"] == 1.0
    two_sites = "".join(f"P{i} ([a](https://a.com/{i})).\n\n" if i % 2 else f"P{i} ([b](https://b.org/{i})).\n\n"
                        for i in range(8))
    even8 = "".join(f"P{i} ([s](https://site{i}.com/x)).\n\n" for i in range(8))
    lean = await SourceDiversity().score(make_archive("# R\n\n## S\n\n" + two_sites), ctx)
    wide = await SourceDiversity().score(make_archive("# R\n\n## S\n\n" + even8), ctx)
    # Two sites split evenly: 1 bit (as diverse as 2 even domains); eight: 3 bits.
    assert lean.value == 1.0 and lean.details["equivalent_domains"] == 2
    assert wide.value == 3.0 and wide.details["equivalent_domains"] == 8
    uncited = await SourceDiversity().score(make_archive("# R\n\n## S\n\nNo links.\n"), ctx)
    assert uncited.details["basis"] == "retrieved" and uncited.value == pytest.approx(1.585, abs=1e-3)
    assert r.details["retrieved"]["entropy"] == pytest.approx(1.585, abs=1e-3)


async def test_source_authority_rules_judge_and_domain_cache(ctx):
    r = await SourceAuthority().score(make_archive(), ctx)
    basis = {b["domain"]: (b["score"], b["basis"]) for b in r.details["breakdown"]}
    assert basis == {"energy.gov": (1.0, "rule"), "reuters.com": (0.8, "rule"),
                     "weather-blog.com": (0.2, "judge")}
    # The report cites only Reuters; the retrieved mean stays in details.
    assert r.value == 0.8 and r.details["basis"] == "citations"
    assert r.details["retrieved_mean"] == pytest.approx((1.0 + 0.8 + 0.2) / 3, abs=1e-3)
    # Second run: the domain verdict comes from the global cache, no new call.
    before = len(ctx.fake.prompts)
    r2 = await SourceAuthority().score(make_archive(), ctx)
    assert len(ctx.fake.prompts) == before
    assert {b["basis"] for b in r2.details["breakdown"] if b["domain"] == "weather-blog.com"} == {"domain_cache"}


async def test_source_authority_weights_by_citation_and_matches_subdomains(ctx):
    report = ("# T\n\n## S\n\nCobalt mining is concentrated in Congo ([Reuters](https://reuters.com/cobalt)).\n\n"
              "Lithium refining sits in China ([DOE](https://energy.gov/lithium)).\n\n"
              "Refining data again ([DOE](https://energy.gov/lithium)).\n\n"
              "The EU rule applies ([ESMA](https://www.esma.europa.eu/x)).\n")
    r = await SourceAuthority().score(make_archive(report), ctx)
    assert {b["domain"]: b["basis"] for b in r.details["breakdown"]}["esma.europa.eu"] == "rule"
    assert r.value == pytest.approx((0.8 + 1.0 + 1.0 + 0.9) / 4, abs=1e-3)
    assert r.details["cited_domains"][0] == ("energy.gov", 2)


async def test_source_authority_without_judge_falls_back():
    r = await SourceAuthority().score(make_archive(), ScoringContext(cache=EvalCache(":memory:")))
    assert r.details["fallback_domains"] == ["weather-blog.com"]


async def test_source_authority_judge_failure_is_skipped(ctx):
    async def broke(prompt):
        raise RuntimeError("429 no credits")
    ctx.judge = Judge(ctx.cache, model="judge-y", complete=broke)
    r = await SourceAuthority().score(make_archive(), ctx)
    assert r.value is None and r.skipped == "judge call failed"
    assert r.llm["errors"] == 1 and r.llm["error_messages"] == ["RuntimeError: 429 no credits"]
    assert r.details["unscored_domains"] == ["weather-blog.com"]


async def test_citation_utilization_is_url_level_and_rule_based():
    ctx = ScoringContext(cache=EvalCache(":memory:"))       # --rules-only: no judge
    r = await CitationUtilization().score(make_archive(), ctx)
    assert r.value == pytest.approx(1 / 3, abs=1e-3)
    assert r.details["uncited_urls"] == [URLS["lithium"], URLS["unused"]]
    assert r.llm is None and not CitationUtilization.uses_llm
    used = {c["chunk_id"]: c["used"] for c in r.details["per_chunk"]}
    cid = {k: _chunk(k)[0] for k in CHUNK_TEXT}
    assert used == {cid["cobalt"]: True, cid["lithium"]: False, cid["unused"]: False}
    assert r.details["chunk_level"] == pytest.approx(1 / 3, abs=1e-3)


async def test_citation_utilization_reads_judged_chunks_from_citation_audit(ctx):
    r = await CitationUtilization().score(make_archive(), ctx)
    cid = {k: _chunk(k)[0] for k in CHUNK_TEXT}
    assert r.value == pytest.approx(1 / 3, abs=1e-3)          # value stays URL-level
    assert r.details["chunks_used_judged"] == [cid["cobalt"]]
    assert r.details["chunk_level_judged"] == pytest.approx(1 / 3, abs=1e-3)
    assert r.llm["shared"] == "citation_audit"


async def test_citation_utilization_uncited_overlap_is_echo_not_use(ctx):
    report = ("# R\n\n## S\n\n"
              "Lithium refining capacity sits mostly in China, according to agency data from 2024.\n\n"
              "Cobalt mining is concentrated in Congo and creates supply risk for battery makers, "
              "but this paragraph cites [Weather](https://weather-blog.com/rain).\n")
    r = await CitationUtilization().score(make_archive(report), ctx)
    by = {c["chunk_id"]: c for c in r.details["per_chunk"]}
    cid = {k: _chunk(k)[0] for k in CHUNK_TEXT}
    # Lithium text is reproduced but its URL is never cited: echoed, not used.
    assert by[cid["lithium"]]["used"] is False and by[cid["lithium"]]["echoed_uncited"] is True
    # The weather page is cited, but by a paragraph that does not match its content.
    assert by[cid["unused"]]["url_cited"] is True and by[cid["unused"]]["used"] is False
    assert r.details["chunks_echoed_uncited"] >= 1


async def test_query_relevance(ctx):
    r = await QueryRelevance().score(make_archive(), ctx)
    scores = {q["query"]: q["score"] for q in r.details["per_query"]}
    assert scores == {"cobalt supply concentration": 0.8, "lithium refining capacity": 0.4}
    assert r.details["no_material"] == ["lithium refining capacity worldwide"]
    assert r.value == pytest.approx(0.6)
    prompt = next(p for p in ctx.fake.prompts if "Sub-query under review:\ncobalt" in p)
    assert "1. cobalt supply" in prompt and "- lithium refining capacity" in prompt
    assert CORE not in prompt.split("Other sub-queries at the same level of the plan:")[1].split("Sub-query under review")[0]


async def test_query_relevance_material_and_initial_search(ctx):
    a = make_archive()
    cid = {k: _chunk(k)[0] for k in CHUNK_TEXT}
    extra = {k + "2": ("https://energy.gov/lithium", "Lithium refining also needs permits.") for k in ["lithium"]}
    for key, (url, text) in extra.items():
        a.data["chunks"][chunk_id(url, text)] = {"url": url, "title": key, "content": text, "jev_score": None}
    a.data["spans"].append({"span_id": "s8", "parent_id": "s2", "name": "initial_results", "attributes": {
        "query": CORE, "chunk_ids": [cid["lithium"], chunk_id(*extra["lithium2"]), cid["unused"]],
        "proposed_urls": [], "new_urls": []}})
    a = RunArchive(a.data)                      # rebuild cached views
    r = await QueryRelevance().score(a, ctx)
    initial, = [q for q in r.details["per_query"] if q["kind"] == "initial_results"]
    # Two chunks from energy.gov + one from the weather blog: one chunk per URL is shown.
    assert (initial["chunks"], initial["urls_total"], initial["urls_shown"]) == (3, 2, 2)
    prompt = next(p for p in ctx.fake.prompts if "the initial search on this query" in p)
    material = prompt.split("Material retrieved for it:")[1]
    assert material.count("https://energy.gov/lithium") == 1


async def test_retrieval_overlap(ctx):
    r = await RetrievalOverlap().score(make_archive(), ctx)
    assert (r.details["proposed"], r.details["new"]) == (6, 4)
    assert r.value == pytest.approx(2 / 6, abs=1e-3)


async def test_llm_metrics_skip_without_judge():
    c = ScoringContext(cache=EvalCache(":memory:"))
    for m in (DecompositionCoverage(), DecompositionTreeQuality(), QueryRelevance()):
        r = await m.score(make_archive(), c)
        assert r.value is None and r.skipped


async def test_score_archive_lists_every_metric_and_is_reproducible(ctx, tmp_path):
    metrics = all_metrics()
    first = await score_archive(make_archive(), metrics, ctx)
    calls = len(ctx.fake.prompts)
    second = await score_archive(make_archive(), metrics, ctx)
    assert len(ctx.fake.prompts) == calls              # everything replayed from cache
    for v in second["metrics"].values():
        if v["llm"]:
            assert v["llm"]["api_calls"] == 0 and v["llm"]["cache_hits"] == v["llm"]["requests"]
    assert set(first["metrics"]) == {m.name for m in metrics}
    assert "overall" not in first and "total" not in first
    strip = lambda rec: {k: (v["value"], v["skipped"]) for k, v in rec["metrics"].items()}
    assert strip(first) == strip(second)
    assert all(v["skipped"] is None for v in first["metrics"].values()), {
        k: v["skipped"] for k, v in first["metrics"].items() if v["skipped"]}
    path = save_results(first, tmp_path)
    assert path == tmp_path / "run-1" / f"{first['scorer_version']}.json"


async def test_scorer_version_tracks_metric_changes():
    a = scorer_version(all_metrics())
    m = all_metrics()
    m[0].version = "99"
    assert scorer_version(m) != a


async def test_metric_crash_is_recorded_not_raised(ctx):
    class Broken(SourceDiversity):
        name = "broken"

        async def score(self, archive, ctx):
            raise RuntimeError("nope")

    rec = await score_archive(make_archive(), [Broken()], ctx)
    assert rec["metrics"]["broken"]["skipped"].startswith("error: RuntimeError")


def test_query_layer_counts_researchers_and_plans():
    spans = [
        {"span_id": "r0", "parent_id": None, "name": "research", "attributes": {"query": CORE}},
        {"span_id": "p0", "parent_id": "r0", "name": "plan", "attributes": {"query": CORE}},
        {"span_id": "q1", "parent_id": "p0", "name": "sub_query", "attributes": {"query": "a"}},
        {"span_id": "q0", "parent_id": "p0", "name": "sub_query", "attributes": {"query": CORE}},
        {"span_id": "d1", "parent_id": "r0", "name": "deep_level", "attributes": {"query": CORE}},
        {"span_id": "r1", "parent_id": "d1", "name": "research", "attributes": {"query": "a"}},
        {"span_id": "i1", "parent_id": "r1", "name": "initial_results", "attributes": {"query": "a"}},
        {"span_id": "p1", "parent_id": "r1", "name": "plan", "attributes": {"query": "a"}},
        {"span_id": "q2", "parent_id": "p1", "name": "sub_query", "attributes": {"query": "a"}},
        {"span_id": "q3", "parent_id": "p1", "name": "sub_query", "attributes": {"query": "a.1"}},
        # A detailed report's subtopic researcher: a root span with parent_query.
        {"span_id": "r2", "parent_id": None, "name": "research",
         "attributes": {"query": "b", "parent_query": CORE}},
        {"span_id": "p2", "parent_id": "r2", "name": "plan", "attributes": {"query": "b"}},
        {"span_id": "q4", "parent_id": "p2", "name": "sub_query", "attributes": {"query": "b.1"}},
    ]
    a = RunArchive(build_archive(meta={"run_id": "t", "query": CORE}, spans=spans,
                                 chunks={}, report_markdown="# t\n"))
    layers = {s: a.query_layer(s) for s in ("q0", "q1", "i1", "q2", "q3", "q4")}
    assert layers == {"q0": 0, "q1": 1, "i1": 1, "q2": 1, "q3": 2, "q4": 2}


async def test_query_relevance_compares_only_the_same_layer(ctx):
    a = make_archive()
    cid = {k: _chunk(k)[0] for k in CHUNK_TEXT}
    a.data["spans"] += [
        {"span_id": "s8", "parent_id": "s2", "name": "research",
         "attributes": {"query": "cobalt supply concentration"}},
        {"span_id": "s9", "parent_id": "s8", "name": "plan", "attributes": {"query": "cobalt"}},
        {"span_id": "s10", "parent_id": "s9", "name": "sub_query", "attributes": {
            "query": "cobalt mine ownership Congo", "chunk_ids": [cid["cobalt"]]}},
    ]
    a = RunArchive(a.data)
    r = await QueryRelevance().score(a, ctx)
    layer = {q["query"]: q["layer"] for q in r.details["per_query"]}
    assert layer == {"cobalt supply concentration": 1, "lithium refining capacity": 1,
                     "cobalt mine ownership Congo": 2}
    others = lambda q: next(p for p in ctx.fake.prompts if f"Sub-query under review:\n{q}" in p
                            ).split("same level of the plan:")[1].split("Sub-query under review")[0]
    assert "cobalt mine ownership" not in others("cobalt supply concentration")
    assert others("cobalt mine ownership Congo").strip() == "(none)"


def test_concentration_measures():
    from evals.research_eval.metrics.retrieval.source import concentration
    even = concentration(["a", "b", "c", "d"])
    assert even["hhi"] == 0.25 and even["effective"] == 4 and even["entropy"] == 2 and even["evenness"] == 1
    skewed = concentration(["a"] * 8 + ["b", "c"])          # shares .8 .1 .1
    assert skewed["hhi"] == pytest.approx(0.66) and skewed["effective"] == pytest.approx(1.515, abs=1e-3)
    assert skewed["gini_simpson"] == pytest.approx(0.34)
    assert skewed["entropy"] == pytest.approx(0.922, abs=1e-3)


async def test_source_diversity_reports_retrieved_and_cited_concentration():
    r = await SourceDiversity().score(make_archive(), ScoringContext(cache=EvalCache(":memory:")))
    assert r.details["retrieved"]["domains"] == 3
    assert r.details["cited"]["n"] == 1 and r.details["cited"]["hhi"] == 1


async def test_citation_utilization_reasoning_chain_for_deep_research():
    rules_ctx = ScoringContext(cache=EvalCache(":memory:"))
    a = make_archive("# R\n\n## S\n\n"
                     "Lithium refining capacity sits mostly in China, according to agency data from 2024.\n\n"
                     "Cobalt mining is concentrated in Congo and creates supply risk for battery makers, "
                     "but this paragraph cites [Weather](https://weather-blog.com/rain).\n")
    assert "reasoning" not in (await CitationUtilization().score(a, rules_ctx)).details
    a.data["spans"][1]["attributes"]["learnings"] = [
        "Lithium refining capacity sits mostly in China.",          # rests on the lithium chunk
        "Rain is expected across northern regions this weekend."]   # rests on the weather chunk
    a = RunArchive(a.data)
    r = await CitationUtilization().score(a, rules_ctx)
    chain = r.details["reasoning"]
    assert chain["learnings"] == 2 and chain["chunks_distilled"] == 2
    # Only the lithium learning reaches the report, so only its chunk counts.
    assert chain["learnings_in_report"] == 1 and chain["chunks_via_learnings"] == 1
    assert chain["chunk_level"] == pytest.approx(1 / 3, abs=1e-3)
