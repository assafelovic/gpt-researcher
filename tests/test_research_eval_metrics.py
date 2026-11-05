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
    SourceUtilization, DecompositionCoverage, DecompositionTreeQuality, PlanAdherence,
    MaterialCoverage, QueryRelevance, RetrievalOverlap, SourceAuthority, SourceDiversity,
    SourceRecency, SubqueryRedundancy)
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
        self.asked = {}

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
        if "planning research on one query" in prompt:
            # The aspects of a parent below the question, listed without its children.
            q = prompt.split("Query:\n")[1].split("\n")[0]
            if "garbled" in q:
                return "not json"
            return json.dumps({"aspects": ["output figures", "mining sites", "labour conditions"]})
        if "List the distinct aspects" in prompt:
            return json.dumps({"key_points": ["cobalt supply", "lithium refining", "recycling policy"]})
        if "retrieved covers, before any report" in prompt:
            # Covered when one of the point's own passages names its first word.
            blocks = prompt.split("Key point ")[1:]
            out = []
            for b in blocks:
                n, rest = b.split(":", 1)
                word = rest.split()[0].lower()
                ids = [i for i, text in re.findall(r"^\[(\w+)\] [^\n]*\n([^\n]*)", rest, re.M)
                       if word in text.lower()]
                out.append({"point": int(n), "coverage": "full" if ids else "none", "passages": ids})
            return json.dumps({"points": out[:-1] if "drop-last" in prompt else out})
        if "which aspects of a research question" in prompt:
            points = re.findall(r"^(\d+)\. (.+)$", prompt.split("Key points:")[1].split("Sub-queries:")[0], re.M)
            subs = re.findall(r"^(\d+)\. (.+)$", prompt.split("Sub-queries:")[1].split("Return ONLY")[0], re.M)
            return json.dumps({"points": [
                {"point": int(i), "evidence": "",
                 "subqueries": [int(j) for j, q in subs if p.split()[0] in q]} for i, p in points]})
        if "how a research agent split a query" in prompt:
            # Every child passes, except that "sodium" serves neither the parent nor the
            # question; an aspect is picked up by the children that name its first word.
            kids = re.findall(r"^(\d+)\. (.+)$", prompt.split("Child queries:\n")[1].split("\n\n")[0], re.M)
            aspects = re.findall(r"^(\d+)\. (.+)$", prompt.split("Aspects of the parent:\n")[1].split("\n\n")[0],
                                 re.M)
            return json.dumps({
                "children": [{"child": int(n), "narrower": True, "searchable": "yes",
                              "serves_parent": "sodium" not in q, "serves_question": "sodium" not in q,
                              "evidence": q} for n, q in kids],
                "aspects": [{"aspect": int(i), "children": [str(n) for n, q in kids if a.split()[0] in q.lower()]}
                            for i, a in aspects]})
        if "auditing the search plan of a research agent" in prompt:
            # A query repeats the first earlier one it starts with (ancestors included:
            # the metric must drop those marks).
            qs = re.findall(r"^(\d+)\.(?: \[[^\]]*\])? (.+)$", prompt.split("Queries:\n")[1].split("Return ONLY")[0], re.M)
            if any("garbled" in q for _, q in qs):
                return "not json"
            # "flaky" queries are marked on the first call only, "flaky2" on the first two.
            self.asked[prompt] = self.asked.get(prompt, 0) + 1
            out = []
            for n, q in qs:
                rep = next((int(m) for m, p in qs if int(m) < int(n) and q.startswith(p)), None)
                if ("flaky2" in q and self.asked[prompt] > 2) or ("flaky2" not in q and "flaky" in q
                                                                  and self.asked[prompt] > 1):
                    rep = None
                out.append({"query": int(n), "evidence": "", "repeats": rep})
            return json.dumps({"queries": out[:-1] if any("drop-last" in q for _, q in qs) else out})
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


async def test_subquery_redundancy_judges_every_node_in_one_call(ctx):
    r = await SubqueryRedundancy().score(make_archive(), ctx)
    # The core repeat (layer 0) is the run's question, not a node; the step
    # that brought back no new material is still a node.
    assert r.details["method"] == "judge_tree" and r.details["nodes"] == 3
    [d] = r.details["not_unique"]
    assert (d["query"], d["repeats"]) == ("lithium refining capacity worldwide", "lithium refining capacity")
    assert d["same_parent"] is True and d["same_layer"] is True and d["kind"] == "leaf"
    assert r.value == pytest.approx(1 / 3, abs=1e-3) and r.higher_is_better is False
    assert sum("auditing the search plan" in p for p in ctx.fake.prompts) == 3     # three votes
    assert r.details["votes"] == 3 and r.details["replies"] == 3 and r.details["unstable"] == []
    assert r.llm["prompts"]["subquery_redundancy"]["version"] == "5"


async def test_subquery_redundancy_takes_the_majority_of_three_calls(ctx):
    a = nested_archive(" flaky2")
    next(x for x in a.data["spans"] if x["span_id"] == "s6")["attributes"]["query"] = \
        "lithium refining capacity worldwide flaky"
    r = await SubqueryRedundancy().score(RunArchive(a.data), ctx)
    assert r.details["replies"] == 3
    assert {u["query"]: (u["marks"], u["counted"]) for u in r.details["unstable"]} == {
        "lithium refining capacity worldwide flaky": (1, False), "lithium refining capacity in Europe flaky2": (2, True)}
    assert {u["repeats"] for u in r.details["unstable"]} == {"lithium refining capacity"}
    dups = {d["query"] for d in r.details["not_unique"]}
    assert dups == {"Congo cobalt output 2024 figures", "lithium refining capacity in Europe flaky2"}


def nested_archive(extra=""):
    """make_archive plus two subtopic researchers (layer 1 branches) with their
    own sub-queries (layer 2): one repeats a sub-query of the other branch, one
    a layer-1 sub-query, one only rewords its own parent."""
    a = make_archive()
    cobalt = _chunk("cobalt")[0]

    def step(sid, parent, name, query, **attrs):
        a.data["spans"].append({"span_id": sid, "parent_id": parent, "name": name, "attributes": {
            "query": query, "chunk_ids": [cobalt], "proposed_urls": [], "new_urls": [], **attrs}})

    for rid, q, subs in [("t1", "Congo cobalt mining", ["Congo cobalt output 2024", "Congo cobalt mining sites"]),
                         ("t2", "recycling policy in Europe", ["Congo cobalt output 2024 figures",
                                                               "lithium refining capacity in Europe" + extra])]:
        a.data["spans"].append({"span_id": rid, "parent_id": "s1", "name": "research",
                                "attributes": {"query": q, "parent_query": CORE}})
        step(rid + "i", rid, "initial_results", q)
        a.data["spans"].append({"span_id": rid + "p", "parent_id": rid, "name": "plan",
                                "attributes": {"query": q, "sub_queries": subs}})
        for k, sq in enumerate(subs):
            step(f"{rid}s{k}", rid + "p", "sub_query", sq)
    step("t1r", "t1p", "sub_query", "Congo cobalt mining", is_core_query=True)   # repeat: same node
    return RunArchive(a.data)


async def test_subquery_redundancy_compares_across_branches_and_layers_but_not_ancestors(ctx):
    a = nested_archive()
    kinds = {(n.layer, n.kind, n.parent) for n in a.query_nodes}
    assert kinds == {(1, "leaf", "s2"), (1, "branch", "s2"), (2, "leaf", "t1"), (2, "leaf", "t2")}
    assert a.query_node_ancestors["t1s1"] == ["t1i"] and a.query_node_ancestors["t1i"] == []
    r = await SubqueryRedundancy().score(a, ctx)
    [prompt] = {p for p in ctx.fake.prompts if "auditing the search plan" in p}     # one prompt, asked 3 times
    assert "6. [4] Congo cobalt mining sites" in prompt and "4. Congo cobalt mining" in prompt
    assert r.details["nodes"] == 9 and r.details["duplicates"] == 3
    assert r.value == pytest.approx(3 / 9, abs=1e-3)
    # Rewording its own parent is not a repeat: the mark is dropped.
    assert r.details["dropped_marks"] == [{"query": "Congo cobalt mining sites", "marked": "Congo cobalt mining"}]
    dup = {d["query"]: d for d in r.details["not_unique"]}
    assert dup["Congo cobalt output 2024 figures"]["same_parent"] is False
    assert dup["Congo cobalt output 2024 figures"]["same_layer"] is True
    assert (dup["lithium refining capacity in Europe"]["repeats_layer"], dup["lithium refining capacity in Europe"]["layer"]) == (1, 2)
    assert r.details["same_layer"] == 2 and r.details["same_parent"] == 1
    assert r.details["per_layer"] == {1: {"nodes": 5, "duplicates": 1, "share": 0.2},
                                      2: {"nodes": 4, "duplicates": 2, "share": 0.5}}
    assert r.details["per_kind"] == {"branch": {"nodes": 2, "duplicates": 0, "share": 0.0},
                                     "leaf": {"nodes": 7, "duplicates": 3, "share": 0.429}}


async def test_subquery_redundancy_reports_skipped_nodes_and_failed_calls(ctx):
    r = await SubqueryRedundancy().score(nested_archive(" drop-last"), ctx)
    assert r.details["unanswered"] == ["lithium refining capacity in Europe drop-last"]
    assert r.details["nodes"] == 9 and r.details["duplicates"] == 2 and r.llm["errors"] == 0
    r = await SubqueryRedundancy().score(nested_archive(" garbled"), ctx)
    assert r.value is None and r.skipped == "judge call failed"


async def test_subquery_redundancy_lexical_fallback_flags_near_duplicates():
    ctx = ScoringContext(cache=EvalCache(":memory:"))       # no judge
    r = await SubqueryRedundancy().score(make_archive(), ctx)
    assert r.details["method"] == "lexical" and r.details["pairs"] == 6
    pairs = {(d["a"], d["b"]) for d in r.details["duplicate_pairs"]}
    assert pairs == {("lithium refining capacity", "lithium refining capacity worldwide")}
    assert r.value == pytest.approx(1 / 6, abs=1e-3)
    assert r.higher_is_better is False


async def test_tree_quality_judges_each_child_and_the_aspects_of_the_split(ctx):
    r = await DecompositionTreeQuality().score(make_archive(), ctx)
    # Checks over 4 children: 1, 1, 0.75, 0.75; the split of the question is held
    # against its key points, and 2 of 3 are picked up (recycling is not).
    assert r.value == pytest.approx((1 + 1 + 0.75 + 0.75 + 2 / 3) / 5, abs=1e-3)
    assert r.details["checks"] == {"narrower": 1.0, "searchable": 1.0, "serves_parent": 0.75,
                                   "serves_question": 0.75}
    assert r.details["coverage"] == 0.667 and r.details["children"] == 4
    [w] = r.details["weak_children"]
    assert w["child"] == "sodium battery alternatives" and w["failed"] == ["serves_parent", "serves_question"]
    [p] = r.details["per_parent"]
    assert p["aspects"] == [{"aspect": "cobalt supply", "source": "key_points", "children": [1]},
                            {"aspect": "lithium refining", "source": "key_points", "children": [2, 3]},
                            {"aspect": "recycling policy", "source": "key_points", "children": []}]
    assert p["unanswered_aspects"] == 0
    assert r.details["uncovered_aspects"] == [{"parent": CORE, "aspect": "recycling policy"}]
    assert r.details["key_points"]["source"] == "judge"
    # The key points are shared with decomposition_coverage, so the metric itself asks once.
    assert r.llm["requests"] == r.llm["api_calls"] == 1 and r.llm["judge_model"] == "judge-x"
    assert r.llm["prompts"]["tree_quality"]["version"] == "8"
    assert not any("planning research on one query" in q for q in ctx.fake.prompts)
    prompt = next(p for p in ctx.fake.prompts if "Path from the original question" in p)
    assert f"0. {CORE}" in prompt and r.details["per_parent"][0]["depth"] == 0
    assert f"Original research question (the root of the whole search tree):\n{CORE}" in prompt
    assert "4. sodium battery alternatives" in prompt
    assert "Aspects of the parent:\n1. cobalt supply\n2. lithium refining\n3. recycling policy" in prompt


async def test_tree_quality_lists_the_aspects_of_a_lower_parent_before_its_children(ctx):
    r = await DecompositionTreeQuality().score(nested_archive(), ctx)
    by = {p["parent"]: p for p in r.details["per_parent"]}
    assert set(by) == {CORE, "Congo cobalt mining", "recycling policy in Europe"}
    asked = [q for q in ctx.fake.prompts if "planning research on one query" in q]
    assert len(asked) == 2
    # The aspects are listed from the parent alone: its children are not in that prompt.
    one = next(q for q in asked if q.endswith("Query:\nCongo cobalt mining"))
    assert "Congo cobalt mining sites" not in one and f"Original research question" in one
    cobalt = by["Congo cobalt mining"]
    assert [a["source"] for a in cobalt["aspects"]] == ["judge"] * 3
    assert [a["children"] for a in cobalt["aspects"]] == [[1], [2], []]
    assert cobalt["coverage"] == 0.667
    assert by["recycling policy in Europe"]["coverage"] == 0.333
    assert r.llm["requests"] == 5          # 3 splits + 2 aspect lists


async def test_dry_run_counts_follow_up_requests_and_caches_nothing():
    cache = EvalCache(":memory:")
    j = Judge(cache, model="m", dry_run=True)
    r = await DecompositionTreeQuality().score(nested_archive(), ScoringContext(cache=cache, judge=j))
    # key points + 2 aspect lists + 3 splits: the splits below the question are
    # asked only once their aspects are known, so a dry run must answer them.
    assert j.calls == 6 and r.value is not None
    j2 = Judge(cache, model="m", dry_run=True)
    await DecompositionTreeQuality().score(nested_archive(), ScoringContext(cache=cache, judge=j2))
    assert j2.calls == 6 and j2.cache_hits == 0


async def test_tree_quality_children_cannot_redefine_the_aspects(ctx):
    # Three near-identical children: v4 let the judge list one aspect next to them,
    # fully covered. The key points are fixed first, so the collapse shows.
    a = make_archive()
    a.data["spans"][2]["attributes"]["sub_queries"] = [
        "cobalt supply risk", "cobalt supply risks 2024", "risks to cobalt supply"]
    r = await DecompositionTreeQuality().score(RunArchive(a.data), ctx)
    [p] = r.details["per_parent"]
    assert [x["children"] for x in p["aspects"]] == [[1, 2, 3], [], []]
    assert p["coverage"] == 0.333


async def test_tree_quality_reports_a_parent_without_aspects(ctx):
    a = nested_archive()
    for s in a.data["spans"]:
        if s["span_id"] == "t2p":
            s["attributes"]["query"] = "recycling policy in Europe garbled"
    r = await DecompositionTreeQuality().score(RunArchive(a.data), ctx)
    bad = next(p for p in r.details["per_parent"] if "garbled" in p["parent"])
    assert bad["score"] is None and bad["aspects"] == [] and bad["error"]
    assert r.details["scored_parents"] == 2 and r.llm["errors"] == 1


async def test_tree_quality_leaves_out_deep_clarifying_questions(ctx):
    a = make_archive()
    a.data["spans"].append({"span_id": "q9", "parent_id": "s2", "name": "deep_plan",
                            "attributes": {"query": CORE, "questions": ["Which regions?", "Which years?"]}})
    r = await DecompositionTreeQuality().score(RunArchive(a.data), ctx)
    assert [p["kind"] for p in r.details["per_parent"]] == ["plan"]


def test_query_path_runs_from_the_question_down():
    spans = [
        {"span_id": "r0", "parent_id": None, "name": "research", "attributes": {"query": CORE}},
        {"span_id": "d1", "parent_id": "r0", "name": "deep_level", "attributes": {"query": CORE}},
        {"span_id": "r1", "parent_id": "d1", "name": "research", "attributes": {"query": "a"}},
        {"span_id": "p1", "parent_id": "r1", "name": "plan", "attributes": {"query": "a"}},
        {"span_id": "r2", "parent_id": None, "name": "research",
         "attributes": {"query": "b", "parent_query": CORE}},
    ]
    a = RunArchive(build_archive(meta={"run_id": "t", "query": CORE}, spans=spans,
                                 chunks={}, report_markdown="# t\n"))
    assert a.query_path("p1") == [CORE, "a"]
    assert a.query_path("r2") == [CORE, "b"]


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
    # Two sites split evenly: two random citations differ 4 times in 7
    # (8/7 x 0.5); eight different sites: always. Both are perfectly even, so
    # evenness alone would score them the same.
    assert lean.value == pytest.approx(0.571, abs=1e-3) and lean.details["equivalent_domains"] == 2
    assert wide.value == 1.0 and wide.details["equivalent_domains"] == 8
    assert lean.details["evenness"] == wide.details["evenness"] == 1.0
    assert (lean.details["entropy"], wide.details["entropy"]) == (1.0, 3.0)
    # Twice as long with the same two-site split: about the same, not higher.
    two_sites16 = "".join(f"P{i} ([a](https://a.com/{i})).\n\n" if i % 2 else f"P{i} ([b](https://b.org/{i})).\n\n"
                          for i in range(16))
    twice = await SourceDiversity().score(make_archive("# R\n\n## S\n\n" + two_sites16), ctx)
    assert twice.value == pytest.approx(0.533, abs=1e-3)
    uncited = await SourceDiversity().score(make_archive("# R\n\n## S\n\nNo links.\n"), ctx)
    # Nothing cited: 0, not the retrieved sources' spread (which stays in details).
    assert uncited.details["basis"] == "no body citations" and uncited.value == 0.0
    assert uncited.details["retrieved"]["domains"] == 3
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


async def test_source_authority_skips_a_report_that_cites_nothing(ctx):
    r = await SourceAuthority().score(make_archive("# R\n\n## S\n\nNo links.\n"), ctx)
    assert r.value is None and r.skipped == "no body citations"
    assert r.details["retrieved_mean"] is not None


async def test_source_authority_judge_failure_is_skipped(ctx):
    async def broke(prompt):
        raise RuntimeError("429 no credits")
    ctx.judge = Judge(ctx.cache, model="judge-y", complete=broke)
    r = await SourceAuthority().score(make_archive(), ctx)
    assert r.value is None and r.skipped == "judge call failed"
    assert r.llm["errors"] == 1 and r.llm["error_messages"] == ["RuntimeError: 429 no credits"]
    assert r.details["unscored_domains"] == ["weather-blog.com"]


async def test_source_utilization_is_url_level_and_rule_based():
    ctx = ScoringContext(cache=EvalCache(":memory:"))       # --rules-only: no judge
    r = await SourceUtilization().score(make_archive(), ctx)
    assert r.value == pytest.approx(1 / 3, abs=1e-3)
    assert r.details["uncited_urls"] == [URLS["lithium"], URLS["unused"]]
    assert r.llm is None and not SourceUtilization.uses_llm
    used = {c["chunk_id"]: c["used"] for c in r.details["per_chunk"]}
    cid = {k: _chunk(k)[0] for k in CHUNK_TEXT}
    assert used == {cid["cobalt"]: True, cid["lithium"]: False, cid["unused"]: False}
    assert r.details["chunk_level"] == pytest.approx(1 / 3, abs=1e-3)


async def test_source_utilization_reads_judged_chunks_from_citation_audit(ctx):
    r = await SourceUtilization().score(make_archive(), ctx)
    cid = {k: _chunk(k)[0] for k in CHUNK_TEXT}
    assert r.value == pytest.approx(1 / 3, abs=1e-3)          # value stays URL-level
    assert r.details["chunks_used_judged"] == [cid["cobalt"]]
    assert r.details["chunk_level_judged"] == pytest.approx(1 / 3, abs=1e-3)
    assert r.llm["shared"] == "citation_audit"


async def test_source_utilization_uncited_overlap_is_echo_not_use(ctx):
    report = ("# R\n\n## S\n\n"
              "Lithium refining capacity sits mostly in China, according to agency data from 2024.\n\n"
              "Cobalt mining is concentrated in Congo and creates supply risk for battery makers, "
              "but this paragraph cites [Weather](https://weather-blog.com/rain).\n")
    r = await SourceUtilization().score(make_archive(report), ctx)
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


async def test_source_utilization_reasoning_chain_for_deep_research():
    rules_ctx = ScoringContext(cache=EvalCache(":memory:"))
    a = make_archive("# R\n\n## S\n\n"
                     "Lithium refining capacity sits mostly in China, according to agency data from 2024.\n\n"
                     "Cobalt mining is concentrated in Congo and creates supply risk for battery makers, "
                     "but this paragraph cites [Weather](https://weather-blog.com/rain).\n")
    assert "reasoning" not in (await SourceUtilization().score(a, rules_ctx)).details
    a.data["spans"][1]["attributes"]["learnings"] = [
        "Lithium refining capacity sits mostly in China.",          # rests on the lithium chunk
        "Rain is expected across northern regions this weekend."]   # rests on the weather chunk
    a = RunArchive(a.data)
    r = await SourceUtilization().score(a, rules_ctx)
    chain = r.details["reasoning"]
    assert chain["learnings"] == 2 and chain["chunks_distilled"] == 2
    # Only the lithium learning reaches the report, so only its chunk counts.
    assert chain["learnings_in_report"] == 1 and chain["chunks_via_learnings"] == 1
    assert chain["chunk_level"] == pytest.approx(1 / 3, abs=1e-3)
    # Without learning_sources there is no URL-level funnel.
    assert chain["learning_urls"] is None


async def test_source_utilization_url_funnel_for_deep_research():
    rules_ctx = ScoringContext(cache=EvalCache(":memory:"))
    a = make_archive("# R\n\n## S\n\n"
                     "Lithium refining capacity sits mostly in China, according to agency data from 2024 "
                     f"([lithium]({URLS['lithium']})).\n")
    lithium = "Lithium refining capacity sits mostly in China."
    cobalt = "Cobalt mining is concentrated in Congo."
    a.data["spans"][1]["attributes"]["learnings"] = [lithium, cobalt]
    a.data["spans"][1]["attributes"]["learning_sources"] = {
        lithium: URLS["lithium"], cobalt: URLS["cobalt"]}
    chain = (await SourceUtilization().score(RunArchive(a.data), rules_ctx)).details["reasoning"]
    assert chain["retrieved_urls"] == 3
    assert chain["learning_urls"] == 2 and chain["cited_learning_urls"] == 1
    assert chain["cited_other_urls"] == 0


async def test_failed_runs_are_skipped_unless_asked(ctx):
    from evals.research_eval.scoring import run_failure
    a = make_archive("# R\n\nI could not gather any source material for this question.\n")
    assert "no real report" in run_failure(a)
    record = await score_archive(a, all_metrics(), ctx)
    assert record["run_status"] == "failed"
    assert all(r["value"] is None and r["skipped"].startswith("failed run") for r in record["metrics"].values())
    record = await score_archive(a, [m for m in all_metrics() if m.name == "plan_adherence"], ctx, score_failed=True)
    assert record["metrics"]["plan_adherence"]["value"] is not None
    a.data["meta"]["status"], a.data["meta"]["error"] = "error", "boom"
    assert "boom" in run_failure(RunArchive(a.data))
    assert run_failure(make_archive()) is None


async def test_judge_counts_tokens_from_usage_metadata():
    j = Judge(EvalCache(":memory:"), model="m", complete=lambda p: None)
    j._add_usage({"input_tokens": 10, "output_tokens": 3})
    j._add_usage(None)
    assert j.usage() == {"model": "m", "calls": 0, "cache_hits": 0, "input_tokens": 10, "output_tokens": 3,
                         "prompt_chars": 0, "refused": 0}


async def test_reasoning_chain_leaves_out_chunks_of_deeper_levels():
    rules_ctx = ScoringContext(cache=EvalCache(":memory:"))
    a = make_archive("# R\n\n## S\n\n"
                     "Lithium refining capacity sits mostly in China, according to agency data from 2024.\n")
    a.data["spans"][1]["attributes"]["learnings"] = ["Lithium refining capacity sits mostly in China."]
    base = (await SourceUtilization().score(RunArchive(a.data), rules_ctx)).details["reasoning"]
    assert base["chunks_distilled"] == 1
    # Move the lithium sub-query under a deeper level of the same step: its chunk
    # was retrieved after the learning was written, so it cannot back it.
    a.data["spans"].append({"span_id": "dl", "parent_id": "s2", "name": "deep_level", "attributes": {"query": CORE}})
    for sp in a.data["spans"]:
        if sp["span_id"] == "s5":
            sp["parent_id"] = "dl"
    chain = (await SourceUtilization().score(RunArchive(a.data), rules_ctx)).details["reasoning"]
    assert chain["chunks_distilled"] == 0


def test_failed_deep_step_material_is_not_counted_as_reaching_the_writer():
    ca, cb = _chunk("cobalt"), _chunk("lithium")
    spans = [
        {"span_id": "r0", "parent_id": None, "name": "research", "attributes": {"query": CORE}},
        {"span_id": "d1", "parent_id": "r0", "name": "deep_level", "attributes": {"query": CORE}},
        # ok step: learnings recorded (even empty); failed step: none recorded
        {"span_id": "r1", "parent_id": "d1", "name": "research", "attributes": {"query": "a", "learnings": []}},
        {"span_id": "q1", "parent_id": "r1", "name": "sub_query", "attributes": {"query": "a", "chunk_ids": [ca[0]]}},
        {"span_id": "r2", "parent_id": "d1", "name": "research", "attributes": {"query": "b"}},
        {"span_id": "q2", "parent_id": "r2", "name": "sub_query", "attributes": {"query": "b", "chunk_ids": [cb[0], ca[0]]}},
    ]
    a = RunArchive(build_archive(meta={"run_id": "t", "query": CORE}, spans=spans,
                                 chunks={ca[0]: ca[1], cb[0]: cb[1]}, report_markdown="# t\n"))
    assert [s["span_id"] for s in a.failed_deep_steps] == ["r2"]
    # cobalt also came back in the ok step, so it still reaches the writer
    assert a.writer_chunk_ids == [ca[0]]


async def test_plan_adherence_counts_a_failed_deep_step_as_not_completed():
    ca, cb = _chunk("cobalt"), _chunk("lithium")
    spans = [
        {"span_id": "r0", "parent_id": None, "name": "research", "attributes": {"query": CORE}},
        {"span_id": "d1", "parent_id": "r0", "name": "deep_level",
         "attributes": {"query": CORE, "serp_queries": [{"query": "a"}, {"query": "b"}, {"query": "c"}]}},
        {"span_id": "r1", "parent_id": "d1", "name": "research", "attributes": {"query": "a", "learnings": []}},
        {"span_id": "q1", "parent_id": "r1", "name": "sub_query", "attributes": {"query": "a", "chunk_ids": [ca[0]]}},
        # b came back with material, then processing raised: nothing went on
        {"span_id": "r2", "parent_id": "d1", "name": "research",
         "attributes": {"query": "b", "process_error": "ValueError: empty"}},
        {"span_id": "q2", "parent_id": "r2", "name": "sub_query", "attributes": {"query": "b", "chunk_ids": [cb[0]]}},
        # c returned nothing
        {"span_id": "r3", "parent_id": "d1", "name": "research", "attributes": {"query": "c", "learnings": []}},
    ]
    a = RunArchive(build_archive(meta={"run_id": "t", "query": CORE}, spans=spans,
                                 chunks={ca[0]: ca[1], cb[0]: cb[1]}, report_markdown="# t\n"))
    r = await PlanAdherence().score(a, ScoringContext(cache=EvalCache(":memory:")))
    assert (r.details["planned"], r.details["delivered"], r.details["completed"]) == (3, 2, 1)
    assert r.value == pytest.approx(1 / 3, abs=1e-3)
    assert r.details["retrieval_delivery"] == pytest.approx(2 / 3, abs=1e-3)
    assert [f["query"] for f in r.details["failed_after_retrieval"]] == ["b"]
    assert r.details["failed_after_retrieval"][0]["error"] == "ValueError: empty"
    assert [f["query"] for f in r.details["not_delivered"]] == ["c"]
    assert r.details["deep_steps_failed"] == 1


# --- source recency / material coverage -----------------------------------------

def test_source_year_prefers_the_url_date_and_ignores_forecasts():
    from evals.research_eval.metrics.retrieval.source import source_year
    assert source_year("https://x.com/news/2025/03/foo", "", "since 2019, as of 2026", 2026) == (2025, "url")
    assert source_year("https://x.com/files/2023-10/report.pdf", "", "2026", 2026) == (2023, "url")
    assert source_year("https://x.com/a", "Outlook 2024", "by 2030 the market doubles", 2026) == (2024, "text")
    assert source_year("https://x.com/a", "", "1,2019 staff, version 3.2020", 2026) == (None, "none")


async def test_source_recency_counts_dated_cited_sources_only():
    a = make_archive(report="# R\n\n## A\n\nCobalt is concentrated ([R](https://reuters.com/cobalt)). "
                            "Refining sits in China ([D](https://energy.gov/lithium)).\n")
    a.data["meta"]["started_at"] = "2025-06-01T00:00:00+00:00"
    r = await SourceRecency().score(a, ScoringContext(cache=EvalCache(":memory:")))
    # cobalt names 2024 (within a year of 2025); lithium names no year: left out, not old.
    assert r.value == 1.0 and r.details["dated"] == 1 and r.details["undated"] == 1
    assert r.details["undated_urls"] == ["https://energy.gov/lithium"]
    a.data["meta"]["started_at"] = "2026-06-01T00:00:00+00:00"
    old = await SourceRecency().score(a, ScoringContext(cache=EvalCache(":memory:")))
    assert old.value == 0.0 and old.details["old"][0]["year"] == 2024
    none = await SourceRecency().score(make_archive(report="# R\n\n## A\n\nNo links here at all.\n"),
                                       ScoringContext(cache=EvalCache(":memory:")))
    assert none.skipped and none.value is None


async def test_material_coverage_grades_key_points_on_evaluator_picked_passages(ctx):
    r = await MaterialCoverage().score(make_archive(), ctx)
    per = {p["key_point"]: p for p in r.details["per_point"]}
    # cobalt and lithium passages exist; nothing retrieved is about recycling policy.
    assert per["cobalt supply"]["coverage"] == "full" and per["lithium refining"]["coverage"] == "full"
    assert per["recycling policy"]["coverage"] == "none"
    assert r.value == pytest.approx(2 / 3, abs=1e-3)
    assert per["cobalt supply"]["urls"] == ["https://www.reuters.com/cobalt"]
    prompt = next(p for p in ctx.fake.prompts if "retrieved covers" in p)
    assert "Weather forecasts" not in prompt.split("Key point 1:")[1].split("Key point 2:")[0]
    assert r.details["unanswered"] == 0 and r.llm["requests"] == 1


async def test_material_coverage_counts_points_the_reply_skipped(ctx):
    a = make_archive()
    a.data["meta"]["query"] = a.data["meta"]["query"] + " drop-last"
    r = await MaterialCoverage().score(a, ctx)
    assert r.details["unanswered"] == 1 and r.details["per_point"][-1]["coverage"] == "none"
