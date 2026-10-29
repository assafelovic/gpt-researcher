"""Tests for the generation metrics and the shared citation audit of evals/research_eval.

The archive and every judge verdict are written by hand, so each expected
number can be worked out from the fixture.
"""

import json
import re

import pytest

from evals.research_eval.archive import RunArchive, build_archive
from evals.research_eval.cache import EvalCache
from evals.research_eval.chunks import chunk_id
from evals.research_eval.citation_audit import citation_audit
from evals.research_eval.judge import Judge
from evals.research_eval.metrics.base import ScoringContext
from evals.research_eval.metrics.generation import (
    Bias, CitationCoverage, CitationPrecision, CitationRecall, Comprehensiveness,
    EffectiveCitations, FactGrounding, Faithfulness, Insight, InstructionFollowing,
    Readability, TopicRelevance, Toxicity)
from evals.research_eval.metrics.generation.hallucination import fact_tokens
from evals.research_eval.report_parser import cited_sentences, parse_report

CORE = "battery supply chain risks"
URL = {"cobalt": "https://reuters.com/cobalt", "lithium": "https://energy.gov/lithium",
       "recycling": "https://recycle.org/eu", "ghost": "https://never-retrieved.com/x"}
TEXT = {
    "cobalt": "The Democratic Republic of Congo produced 74% of mined cobalt in 2023, "
              "and Glencore is the largest producer.",
    "lithium": "China refines about 65% of the world's lithium, according to the IEA.",
    "recycling": "The EU battery regulation sets recycling targets for lithium from 2027.",
}

REPORT = """# Battery supply chain risks

## Raw materials

Congo produced 74% of mined cobalt in 2023 ([Reuters](https://reuters.com/cobalt)). China refines 65% of lithium ([DOE](https://energy.gov/lithium)) ([Reuters](https://reuters.com/cobalt)).

Recycling mandates in Europe start in 2027 and Glencore will dominate them ([Recycle](https://recycle.org/eu)). Prices will triple by 2030 ([Ghost](https://never-retrieved.com/x)).

Lithium refining is concentrated in China, which makes the supply chain fragile for every battery maker in the region.

## Outlook

Overall, diversifying suppliers looks like the sensible path for manufacturers going forward.

## References

- [Reuters](https://reuters.com/cobalt)
- [DOE](https://energy.gov/lithium)
- [Unused](https://unused.org/x)
"""


def make_archive(report=REPORT, config=None):
    chunks, ids = {}, {}
    for k, t in TEXT.items():
        cid = chunk_id(URL[k], t)
        ids[k] = cid
        chunks[cid] = {"url": URL[k], "title": k, "content": t, "jev_score": None}
    spans = [
        {"span_id": "s1", "parent_id": None, "name": "run", "attributes": {"query": CORE}},
        {"span_id": "s2", "parent_id": "s1", "name": "sub_query",
         "attributes": {"query": "q", "chunk_ids": list(ids.values())}},
    ]
    return RunArchive(build_archive(
        meta={"run_id": "gen-1", "question_id": "q1", "query": CORE,
              "config": config or {"mode": "default", "total_words": 50}},
        spans=spans, chunks=chunks, report_markdown=report))


def audit_reply(prompt):
    """Canned paragraph-audit verdicts, keyed on the paragraph's first words."""
    para = prompt.split("Paragraph (sentences numbered")[1].split("Material:")[0]
    if "Congo produced" in para:
        return {"kind": "factual",
                "claims": [{"claim": "Congo 74% cobalt", "verdict": "supported", "passages": ["1a"]},
                           {"claim": "China refines 65%", "verdict": "inferred_b", "passages": ["2a"]}],
                "sentences": [
                    {"sentence": 1, "supported": True, "citations": [{"source": 1, "alone": True}]},
                    {"sentence": 2, "supported": True, "citations": [
                        {"source": 2, "alone": True, "rest_suffice": False},
                        {"source": 1, "alone": False, "rest_suffice": True}]}]}
    if "Recycling mandates" in para:
        return {"kind": "factual",
                "claims": [{"claim": "starts 2027", "verdict": "supported", "passages": ["1a"]},
                           {"claim": "Glencore dominates", "verdict": "contradicted", "passages": ["1a"]},
                           {"claim": "prices triple", "verdict": "unsupported", "passages": []}],
                # The judge wrongly calls sentence 2 supported: its only source was never retrieved.
                "sentences": [
                    {"sentence": 1, "supported": False, "citations": [{"source": 1, "alone": False}]},
                    {"sentence": 2, "supported": True, "citations": [{"source": 2, "alone": True}]}]}
    if "Lithium refining is concentrated" in para:
        return {"kind": "factual",
                "claims": [{"claim": "China concentration", "verdict": "inferred_a", "passages": ["1a"]}],
                "sentences": []}
    return {"kind": "non_factual", "claims": [{"claim": "ignored", "verdict": "unsupported"}],
            "sentences": []}


class ScriptedJudge:
    def __init__(self):
        self.prompts = []

    async def __call__(self, prompt):
        self.prompts.append(prompt)
        if "checking one paragraph of a research report" in prompt:
            return json.dumps(audit_reply(prompt))
        if "a finished report covers" in prompt:
            return json.dumps({"points": [{"point": 1, "coverage": "full"},
                                          {"point": 2, "coverage": "partial"},
                                          {"point": 3, "coverage": "none"}]})
        if "List the distinct aspects" in prompt:
            return json.dumps({"key_points": ["cobalt mining", "lithium refining", "EU battery regulation"]})
        if "preparing a grading rubric" in prompt:
            return json.dumps({"insight": [{"criterion": "causes", "weight": 0.75},
                                           {"criterion": "trade-offs", "weight": 0.25}],
                               "readability": [{"criterion": "flow"}, {"criterion": "terms"}]})
        if "grading a research report on an absolute scale" in prompt:
            return json.dumps({"scores": [{"id": "I1", "score": 8}, {"id": "I2", "score": 4},
                                          {"id": "R1", "score": 6}, {"id": "R2", "score": 9}]})
        if "whether each paragraph of a research report" in prompt:
            n = len(re.findall(r"^\d+\. ", prompt.split("Paragraphs:")[1], re.M))
            v = ["yes", "no", "idk"] + ["yes"] * n
            return json.dumps({"verdicts": [{"paragraph": i, "verdict": v[i - 1]} for i in range(1, n + 1)]})
        if "screening part of a research report" in prompt:
            return json.dumps({"opinions": [
                {"opinion": "diversifying is sensible", "toxic": False, "bias": False},
                {"opinion": "x", "toxic": False, "bias": True, "bias_type": "geography"},
                {"opinion": "y", "toxic": True, "bias": False},
                {"opinion": "z", "toxic": False, "bias": False}]})
        raise AssertionError(prompt[:80])


@pytest.fixture
def ctx():
    cache = EvalCache(":memory:")
    fake = ScriptedJudge()
    c = ScoringContext(cache=cache, judge=Judge(cache, model="judge-x", complete=fake))
    c.fake = fake
    return c


def audit_prompts(ctx):
    return [p for p in ctx.fake.prompts if "checking one paragraph of a research report" in p]


# --- parser: sentence-level citations -----------------------------------------

def test_cited_sentences_places_links_by_position():
    md = ("# T\n\n## S\n\nCobalt comes mostly from Congo ([A](https://a.com)). "
          "Lithium is refined in China ([B](https://b.com)) and Chile. Prices fell. "
          "([C](https://c.com))\n")
    p = parse_report(md)["sections"][0]["paragraphs"][0]
    got = [(s["text"][:12], s["urls"]) for s in cited_sentences(p)]
    # "Prices fell." is too short and merges with the sentence before it,
    # and so does the trailing "(C)" written after the full stop.
    assert got == [("Cobalt comes", ["https://a.com"]),
                   ("Lithium is r", ["https://b.com", "https://c.com"])]


# --- shared audit ------------------------------------------------------------

async def test_audit_material_and_prompt(ctx):
    audit = await citation_audit(make_archive(), ctx)
    modes = [(p.mode, p.kind) for p in audit.paragraphs]
    assert modes == [("cited", "factual"), ("cited", "factual"), ("uncited", "factual"),
                     ("uncited", "non_factual")]
    first = audit_prompts(ctx)[0] if "Congo produced" in audit_prompts(ctx)[0] else next(
        p for p in audit_prompts(ctx) if "Congo produced" in p)
    assert "2. China refines 65% of lithium (DOE) (Reuters).  (cites: [2], [1])" in first
    assert "Source [1] https://reuters.com/cobalt passage 1a:" in first
    second = next(p for p in audit_prompts(ctx) if "Recycling mandates" in p)
    assert "Source [2] https://never-retrieved.com/x\n(not available" in second
    uncited = next(p for p in audit_prompts(ctx) if "Lithium refining is concentrated" in p)
    assert "cites nothing" in uncited and TEXT["lithium"] in uncited
    # Non-factual paragraph: claims dropped even if the judge returns some.
    assert audit.paragraphs[3].claims == []


async def test_audit_is_shared_across_metrics(ctx):
    a = make_archive()
    for m in (CitationRecall(), CitationPrecision(), EffectiveCitations(), Faithfulness()):
        r = await m.score(a, ctx)
        assert r.llm["shared"] == "citation_audit"
    assert len(audit_prompts(ctx)) == 4          # one call per audited paragraph, once


async def test_citation_recall(ctx):
    r = await CitationRecall().score(make_archive(), ctx)
    # 4 citing sentences; recycling sentence 1 not supported; the ghost-URL
    # sentence is forced unsupported although the judge said supported.
    assert (r.details["citing_sentences"], r.details["supported"]) == (4, 2)
    assert r.value == 0.5
    assert {u["urls"][0] for u in r.details["unsupported"]} == {URL["recycling"], URL["ghost"]}


async def test_citation_precision_follows_alce(ctx):
    r = await CitationPrecision().score(make_archive(), ctx)
    # Citations: S1 reuters (precise), S2 doe (precise) + reuters (irrelevant:
    # not alone, rest suffice), recycling (sentence unsupported), ghost (unsupported).
    assert (r.details["citations"], r.details["precise"], r.details["over_citations"]) == (5, 2, 1)
    assert r.value == 0.4


async def test_effective_citations_is_a_count(ctx):
    r = await EffectiveCitations().score(make_archive(), ctx)
    # reuters in S1 and doe in S2; the ghost URL cannot be effective.
    assert r.value == 2.0 and r.details["effective_urls"] == 2


async def test_faithfulness(ctx):
    r = await Faithfulness().score(make_archive(), ctx)
    # supported 1, inferred_b .4, supported 1, contradicted -1, unsupported 0, inferred_a .5
    assert r.value == pytest.approx((1 + 0.4 + 1 - 1 + 0 + 0.5) / 6, abs=1e-3)
    assert r.details["verdicts"]["contradicted"] == 1
    assert r.details["uncited_factual_paragraphs"] == 1
    assert {f["claim"] for f in r.details["flagged"]} == {"Glencore dominates", "prices triple"}


async def test_audit_judge_failure_is_reported(ctx):
    async def bad(prompt):
        return "not json"
    ctx.judge = Judge(EvalCache(":memory:"), model="judge-y", complete=bad)
    r = await CitationRecall().score(make_archive(), ctx)
    assert r.value is None and r.skipped == "no citing sentences"
    assert len(r.details["failed_paragraphs"]) == 4 and r.llm["errors"] == 4


# --- rule metrics --------------------------------------------------------------

def test_fact_tokens():
    toks = fact_tokens("In 2024, the European Central Bank said MiCA covers 1,200 firms and 3 banks. "
                       "Bitcoin rose 45.3%.")
    assert toks == [("number", "2024"), ("number", "1200"), ("number", "45.3"),
                    ("entity", "European Central Bank"), ("entity", "MiCA")]


async def test_fact_grounding(ctx):
    r = await FactGrounding().score(make_archive(), ctx)
    missing = {p["para_id"]: p["missing"] for p in r.details["per_paragraph"]}
    # Paragraph 1: Congo, 74, 2023, China, 65 all in the cited chunks.
    assert missing["sec1-p1"] == []
    # Paragraph 2: 2027 found; Recycling (sentence start) skipped; Glencore,
    # Europe, Prices... 2030 are not in the recycling chunk.
    assert set(missing["sec1-p2"]) == {"Europe", "Glencore", "2030"}
    assert r.details["paragraphs"] == 2
    assert r.value == pytest.approx(r.details["found"] / r.details["checked"], abs=1e-3)


async def test_citation_coverage(ctx):
    r = await CitationCoverage().score(make_archive(), ctx)
    assert r.value == pytest.approx(2 / 3, abs=1e-3)
    assert r.details["references_not_cited"] == ["unused.org/x"]
    assert r.details["body_not_in_references"] == ["never-retrieved.com/x", "recycle.org/eu"]


async def test_instruction_following(ctx):
    r = await InstructionFollowing().score(make_archive(), ctx)
    c = r.details["checks"]
    assert c["min_words"] and c["single_title"] and c["clean_headings"] and c["references"]
    assert c["no_toc"] and c["in_text_citations"]
    assert c["cites_only_retrieved"] is False
    assert r.details["cited_not_retrieved"] == [URL["ghost"]]
    assert r.value == pytest.approx(6 / 7, abs=1e-3)
    long = await InstructionFollowing().score(make_archive(config={"mode": "default"}), ctx)
    assert long.details["min_words"] == 1200 and long.details["checks"]["min_words"] is False


# --- judged writing metrics ----------------------------------------------------

async def test_comprehensiveness(ctx):
    r = await Comprehensiveness().score(make_archive(), ctx)
    assert r.value == 0.5                         # (1 + 0.5 + 0) / 3
    none = r.details["per_point"][2]
    assert none["coverage"] == "none" and none["retrieved_hint"]["url"] == URL["recycling"]
    assert r.details["omitted_but_retrieved"] == ["EU battery regulation"]
    prompt = next(p for p in ctx.fake.prompts if "a finished report covers" in p)
    assert "https://" not in prompt.split("Report:")[1]


async def test_insight_and_readability_share_one_rubric_and_call(ctx):
    a = make_archive()
    i = await Insight().score(a, ctx)
    r = await Readability().score(a, ctx)
    assert i.value == pytest.approx((0.75 * 8 + 0.25 * 4) / 10)
    assert r.value == pytest.approx((6 + 9) / 2 / 10)      # no weights -> equal
    assert sum("grading a research report" in p for p in ctx.fake.prompts) == 1
    assert sum("preparing a grading rubric" in p for p in ctx.fake.prompts) == 1


async def test_topic_relevance_idk_counts_as_relevant(ctx):
    r = await TopicRelevance().score(make_archive(), ctx)
    assert r.details["paragraphs"] == 4
    assert r.value == 0.75 and [p["para_id"] for p in r.details["off_topic"]] == ["sec1-p2"]


async def test_topic_relevance_batches_long_reports(ctx, monkeypatch):
    monkeypatch.setattr(TopicRelevance, "BATCH_CHARS", 150)
    r = await TopicRelevance().score(make_archive(), ctx)
    assert r.llm["requests"] > 1 and r.details["judged"] == 4


async def test_toxicity_and_bias_share_one_screen(ctx):
    a = make_archive()
    t = await Toxicity().score(a, ctx)
    b = await Bias().score(a, ctx)
    assert (t.value, b.value) == (0.25, 0.25)
    assert t.higher_is_better is False and b.details["flagged"][0]["bias_type"] == "geography"
    assert sum("screening part of a research report" in p for p in ctx.fake.prompts) == 1


async def test_generation_llm_metrics_skip_without_judge():
    c = ScoringContext(cache=EvalCache(":memory:"))
    for m in (Comprehensiveness(), Insight(), TopicRelevance(), CitationRecall(), Faithfulness(), Toxicity()):
        r = await m.score(make_archive(), c)
        assert r.value is None and r.skipped == "no judge configured"


def test_cited_sentences_apa_citation_after_full_stop():
    md = ("# T\n\n## S\n\nThe grandfathering window ended on 1 July 2026. Unlicensed firms must stop. "
          "([Didit, 2026](https://a.com); [Norton Rose Fulbright, n.d.](https://b.com); "
          "[Crypto Council for Innovation, 2026](https://c.com))\n")
    p = parse_report(md)["sections"][0]["paragraphs"][0]
    got = cited_sentences(p)
    # The citation-only fragment (and "n.d." inside it) does not become a sentence.
    assert [len(s["urls"]) for s in got] == [0, 3]
    assert got[1]["text"].startswith("Unlicensed firms must stop.")
