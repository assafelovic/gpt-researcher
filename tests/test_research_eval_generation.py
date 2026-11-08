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
    para = prompt.split("Paragraph (numbered items")[1].split("Material:")[0]
    if "Congo produced" in para:
        return {"kind": "factual",
                "claims": [{"claim": "Congo 74% cobalt", "sentences": [1], "verdict": "supported",
                            "passages": ["1a"]},
                           {"claim": "China refines 65%", "sentences": [2], "verdict": "inferred",
                            "passages": ["2a"]}],
                "sentences": [
                    {"sentence": 1, "supported": True, "citations": [{"source": 1, "alone": True}]},
                    {"sentence": 2, "supported": True, "citations": [
                        {"source": 2, "alone": True, "rest_suffice": False},
                        {"source": 1, "alone": False, "rest_suffice": True}]}]}
    if "Recycling mandates" in para:
        return {"kind": "factual",
                "claims": [{"claim": "starts 2027", "sentences": [1], "verdict": "supported",
                            "passages": ["1a"]},
                           {"claim": "Glencore dominates", "sentences": [1], "verdict": "contradicted",
                            "passages": ["1a"]},
                           {"claim": "prices triple", "sentences": [2], "verdict": "unsupported",
                            "passages": []}],
                # The judge wrongly calls sentence 2 supported: its only source was never retrieved.
                "sentences": [
                    {"sentence": 1, "supported": False, "citations": [{"source": 1, "alone": False}]},
                    {"sentence": 2, "supported": True, "citations": [{"source": 2, "alone": True}]}]}
    if "Lithium refining is concentrated" in para:
        return {"kind": "factual",
                "claims": [{"claim": "China concentration", "verdict": "inferred", "passages": ["1a"]}],
                "sentences": []}
    return {"kind": "non_factual", "claims": [{"claim": "ignored", "verdict": "unsupported"}],
            "sentences": []}


class ScriptedJudge:
    def __init__(self):
        self.prompts = []
        # The recheck confirms the first call's contradiction unless a test says otherwise.
        self.recheck = {"Glencore dominates": {"verdict": "contradicted", "passages": []}}

    async def __call__(self, prompt):
        self.prompts.append(prompt)
        if "checking one paragraph of a research report" in prompt:
            return json.dumps(audit_reply(prompt))
        if "not fully supported by the material checked so far" in prompt:
            # Recheck: unsupported unless a test sets a verdict for a claim.
            claims = re.findall(r"^(\d+)\. (.+)$", prompt.split("Claims:")[1].split("Material:")[0], re.M)
            return json.dumps({"claims": [
                {"claim": int(n), **self.recheck.get(text, {"verdict": "unsupported", "passages": []})}
                for n, text in claims]})
        if "a finished report covers" in prompt:
            return json.dumps({"points": [{"point": 1, "coverage": "full"},
                                          {"point": 2, "coverage": "partial"},
                                          {"point": 3, "coverage": "none"}]})
        if "List the distinct aspects" in prompt or "Write the final list from them" in prompt:
            return json.dumps({"key_points": ["cobalt mining", "lithium refining", "EU battery regulation"]})
        if "preparing a grading rubric" in prompt:
            return json.dumps({"insight": [{"criterion": "causes", "weight": 0.75},
                                           {"criterion": "trade-offs", "weight": 0.25}],
                               "readability": [{"criterion": "flow"}, {"criterion": "terms"}]})
        if "grading a research report on an absolute scale" in prompt:
            return json.dumps({"scores": [{"id": "I1", "score": 8}, {"id": "I2", "score": 4},
                                          {"id": "R1", "score": 6}, {"id": "R2", "score": 9}],
                               "insights": [{"insight": "Supply risk is regional.", "quote": "Congo"}]})
        if "whether each paragraph of a research report" in prompt:
            n = len(re.findall(r"^\d+\. ", prompt.split("Paragraphs:")[1], re.M))
            v = ["yes", "no", "idk"] + ["yes"] * n
            return json.dumps({"verdicts": [{"paragraph": i, "verdict": v[i - 1]} for i in range(1, n + 1)]})
        if "searched the same thing twice" in prompt:
            n = len(re.findall(r"^\d+\.", prompt.split("Queries:\n")[1], re.M))
            return json.dumps({"queries": [{"query": i, "repeats": None} for i in range(1, n + 1)]})
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


async def test_citation_recall_is_per_claim(ctx):
    r = await CitationRecall().score(make_archive(), ctx)
    # 6 fact claims: 5 cited, plus the uncited paragraph's claim, which counts
    # as unsupported. Supported: Congo (reuters) and 2027 (recycle). Not: China
    # (inferred: strict), Glencore (contradicted), prices (unsupported; its
    # only source was never retrieved).
    assert (r.details["cited_claims"], r.details["supported"]) == (5, 2)
    assert r.value == round(2 / 6, 3) and r.details["cited_only"] == 0.4
    assert r.details["supported_elsewhere"] == 0
    assert {u["claim"] for u in r.details["unsupported"]} == {
        "China refines 65%", "Glencore dominates", "prices triple"}
    # Former ALCE per citing unit: 2 of 4 units supported.
    assert r.details["unit_level"] == 0.5
    # 6 factual claims in all (the uncited paragraph's one included).
    assert (r.details["factual_claims"], r.details["cited_share"]) == (6, 0.833)
    assert r.details["supported_of_all_claims"] == 0.333


async def test_citation_precision_is_per_claim(ctx):
    r = await CitationPrecision().score(make_archive(), ctx)
    # Item-URL pairs: S1 reuters (backs Congo), S2 doe + reuters (back no
    # supported claim of S2), recycle (backs 2027), ghost (never retrieved).
    assert (r.details["citations"], r.details["precise"]) == (5, 2)
    assert r.value == 0.4
    assert r.details["unit_level"] == 0.4


async def test_effective_citations_is_evidence_per_1k_words(ctx):
    r = await EffectiveCitations().score(make_archive(), ctx)
    # Evidence: the reuters passage behind Congo and the recycle passage behind
    # 2027; the ghost URL cannot be effective.
    assert r.details["evidence"] == 2 and r.details["effective_urls"] == 2
    assert (r.details["evidence_chunks"], r.details["effective_pairs"]) == (2, 2)
    assert r.value == pytest.approx(2000 / r.details["words"], abs=1e-3)


def test_effective_citations_is_zero_when_facts_go_uncited():
    from evals.research_eval.citation_audit import CitationAudit, ParagraphAudit
    archive = RunArchive(build_archive(
        meta={"run_id": "r", "query": "q"},
        spans=[{"span_id": "s", "parent_id": None, "name": "run", "attributes": {"chunk_ids": []}}],
        chunks={}, report_markdown="# R\n\n## S\n\n" + "word " * 100))
    pa = ParagraphAudit("p", [], "uncited", [], [])
    pa.kind = "factual"
    pa.claims = [{"claim": "Congo mines most cobalt.", "type": "fact", "verdict": "unsupported", "score": 0}]
    r = EffectiveCitations().from_audit(CitationAudit([pa]), archive)
    assert r.value == 0.0 and r.skipped is None and r.details["fact_claims"] == 1
    pa.claims = [{"claim": "This matters.", "type": "analysis", "verdict": "unsupported", "score": 0}]
    assert EffectiveCitations().from_audit(CitationAudit([pa]), archive).skipped == "no fact claims"


def test_effective_citations_merges_near_duplicate_evidence():
    from evals.research_eval.citation_audit import CitationAudit, ParagraphAudit
    copy = "Congo produced 74% of mined cobalt in 2023 and Glencore is the largest producer."
    archive = RunArchive(build_archive(
        meta={"run_id": "r", "query": "q"},
        spans=[{"span_id": "s", "parent_id": None, "name": "run",
                "attributes": {"chunk_ids": ["c1", "c2", "c3"]}}],
        chunks={"c1": {"url": "https://a", "content": copy},
                "c2": {"url": "https://b", "content": copy + " Reported by wire."},
                "c3": {"url": "https://a", "content": "China refines about 65% of the world's lithium."}},
        report_markdown="# R\n\n## S\n\n" + "word " * 200))
    pa = ParagraphAudit("p", [], "cited", [], [])
    pa.claim_checks = [{"supported": True, "backing_chunks": ["c1", "c2"]},
                       {"supported": True, "backing_chunks": ["c3", "c1"]},
                       {"supported": False, "backing_chunks": ["c9"]}]
    pa.citation_checks = [{"para_id": "p", "sentence": 1, "url": "https://a", "claims": 2,
                           "no_claims": False, "precise": True}]
    r = EffectiveCitations().from_audit(CitationAudit([pa]), archive)
    # c1 and c2 are the same text on two sites: one piece of evidence; c3 another.
    assert r.details["evidence"] == 2 and r.details["merged_duplicates"] == 1
    assert r.details["words"] == 200 and r.value == 10.0       # 2 per 200 words


async def test_faithfulness(ctx):
    r = await Faithfulness().score(make_archive(), ctx)
    # supported 1, inferred .5, supported 1, contradicted 0 (counted per
    # paragraph by contradicted_paragraphs), unsupported 0, inferred .5
    assert r.value == pytest.approx((1 + 0.5 + 1 + 0 + 0 + 0.5) / 6, abs=1e-3)
    assert r.details["verdicts"]["contradicted"] == 1
    assert r.details["uncited_factual_paragraphs"] == 1
    assert {f["claim"] for f in r.details["flagged"]} == {"Glencore dominates", "prices triple"}


async def test_audit_judge_failure_is_reported(ctx):
    async def bad(prompt):
        return "not json"
    ctx.judge = Judge(EvalCache(":memory:"), model="judge-y", complete=bad)
    r = await CitationRecall().score(make_archive(), ctx)
    assert r.value is None and r.skipped == "every judge call failed"
    assert len(r.details["failed_paragraphs"]) == 4 and r.llm["errors"] == 4


# --- rule metrics --------------------------------------------------------------

def test_fact_tokens():
    toks = fact_tokens("In 2024, the European Central Bank said MiCA covers 1,200 firms and 3 banks. "
                       "Bitcoin rose 45.3%.")
    assert toks == [("number", "2024"), ("number", "1200"), ("number", "45.3"),
                    ("entity", "European Central Bank"), ("entity", "MiCA")]


def test_found_in_name_variants():
    from evals.research_eval.metrics.generation.hallucination import found_in
    ev = "Each CASP must apply DORA. The European Union adopted it."
    low = ev.lower()
    assert found_in("entity", "CASPs", ev, low)                                # plural ~ singular
    assert found_in("entity", "the European Union", ev, low)
    assert found_in("entity", "Digital Operational Resilience Act", ev, low)   # ~ DORA
    assert not found_in("entity", "ESMA", ev, low)


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
    assert r.details["numbers"]["checked"] + r.details["names"]["checked"] == r.details["checked"]


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
    assert c["complete"] and r.details["ending"]["signals"] == []
    assert r.value == pytest.approx(7 / 8, abs=1e-3)
    long = await InstructionFollowing().score(make_archive(config={"mode": "default"}), ctx)
    assert long.details["min_words"] == 1200 and long.details["checks"]["min_words"] is False
    # Detailed reports get their table of contents from code: not held against the writer.
    detailed = await InstructionFollowing().score(make_archive(config={"mode": "detailed"}), ctx)
    assert "no_toc" not in detailed.details["checks"] and len(detailed.details["checks"]) == 7
    # The writer ran out of tokens mid-heading: the run is "ok", the report is not complete.
    cut = REPORT.split("## Outlook")[0] + "## Outlook\n\nDiversifying suppliers is **the"
    r = await InstructionFollowing().score(make_archive(report=cut), ctx)
    assert r.details["checks"]["complete"] is False and r.details["checks"]["references"] is False
    assert set(r.details["ending"]["signals"]) == {"open_emphasis", "ends_mid_sentence"}


def test_report_ending_signs():
    from evals.research_eval.report_parser import report_ending
    ok = "# T\n\n## A\n\nDone ([x](https://a.com)).\n\n---\n\n## References\n\n- [a](https://a.com)"
    assert report_ending(ok)["complete"] and report_ending(ok)["references"]
    assert report_ending("# T\n\n## A\n\n- item one\n- item two")["complete"]     # lists need no full stop
    assert report_ending("# T\n\n## A\n\nThe factors are:")["signals"] == ["ends_mid_sentence"]
    assert report_ending("# T\n\n## A\n\nText.\n\n## B")["signals"] == ["ends_with_heading"]
    assert report_ending("# T\n\n## A\n\n| a | b |\n|---|---|\n| 1 | 2")["signals"] == ["open_table_row"]
    cut_refs = ok + "\n- [b](https://b.com/pa"
    assert report_ending(cut_refs)["signals"] == ["open_link"]
    assert "open_code_block" in report_ending("# T\n\n## A\n\n```\ncode")["signals"]


# --- judged writing metrics ----------------------------------------------------

async def test_comprehensiveness(ctx):
    r = await Comprehensiveness().score(make_archive(), ctx)
    assert r.value == 0.5                         # (1 + 0.5 + 0) / 3
    none = r.details["per_point"][2]
    assert none["coverage"] == "none" and none["retrieved_hint"]["url"] == URL["recycling"]
    assert r.details["omitted_but_retrieved"] == ["EU battery regulation"]
    assert r.details["unanswered"] == 0 and all(e["answered"] for e in r.details["per_point"])
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
    assert i.details["insights_found"] == [{"insight": "Supply risk is regional.", "quote": "Congo"}]
    assert "insights_found" not in r.details


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
    # one of four opinions flagged for each: a count of 1, a share of 0.25
    assert (t.value, b.value) == (1.0, 1.0)
    assert (t.details["rate"], b.details["rate"]) == (0.25, 0.25)
    assert t.details["per_1k_words"] > 0
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


def test_citation_units_cover_preceding_uncited_sentences():
    from evals.research_eval.citation_audit import citation_units
    md = ("# T\n\n## S\n\nFirst fact stated here plainly. Second fact stated here too. "
          "Third claim with its source ([A](https://a.com)). A closing remark without a source.\n")
    p = parse_report(md)["sections"][0]["paragraphs"][0]
    units = citation_units(p)
    assert [(u["urls"], u.get("sentences")) for u in units] == [(["https://a.com"], 3), ([], None)]
    assert units[0]["text"].startswith("First fact") and units[0]["text"].endswith("(A).")
    assert len(citation_units(p, "sentence")) == 4


TABLE_REPORT = """# Title

## Table of Contents

- Rules
- Outlook

## 1. Rules

### 1.1 Timeline

| Date | Change |
|---|---|
| 30 June 2024 | Stablecoin rules apply |

Sources: ([ESMA, 2026](https://esma.europa.eu/a); [EBA, 2025](https://eba.europa.eu/b))

A sentence about the rules ([ESMA, 2026](https://esma.europa.eu/a)).

([EBA, 2025](https://eba.europa.eu/b))

## References

- [ESMA](https://esma.europa.eu/a)
"""


def test_citation_line_attaches_to_the_block_above_and_toc_is_marked():
    from evals.research_eval.citation_audit import audited_paragraphs, citation_units
    parsed = parse_report(TABLE_REPORT)
    paras = [p for s in parsed["sections"] for p in s["paragraphs"]]
    assert [p["type"] for p in paras] == ["toc", "table", "text"]
    table, text = paras[1], paras[2]
    assert [c["url"] for c in table["citations"]] == ["https://esma.europa.eu/a", "https://eba.europa.eu/b"]
    assert table["text"].endswith("(ESMA, 2026; EBA, 2025)")
    assert all(off <= len(table["text"]) for c in table["citations"] for off in c["offsets"])
    # Each data row is a unit carrying the table's citations; the header is not.
    units = citation_units(table)
    assert len(units) == 1 and "Stablecoin rules apply" in units[0]["text"]
    assert units[0]["text"] == "Date: 30 June 2024 | Change: Stablecoin rules apply"
    assert len(units[0]["urls"]) == 2
    assert {c["url"] for c in text["citations"]} == {"https://esma.europa.eu/a", "https://eba.europa.eu/b"}
    toc_free = [p["type"] for p in audited_paragraphs(make_archive(TABLE_REPORT))]
    assert "toc" not in toc_free


def test_report_text_keeps_the_reports_own_structure():
    from evals.research_eval.metrics.generation.common import report_text
    text, truncated = report_text(make_archive(TABLE_REPORT))
    assert not truncated
    assert text.count("# Title") == 1
    assert "## 1. Rules\n\n### 1.1 Timeline" in text          # a heading with only sub-headings stays
    assert "| Date | Change |\n|---|---|\n| 30 June 2024 | Stablecoin rules apply |" in text
    assert "(ESMA, 2026; EBA, 2025)" in text and "http" not in text
    assert "References" not in text


async def test_score_record_keeps_the_full_citation_audit(ctx):
    from evals.research_eval.scoring import score_archive
    rec = await score_archive(make_archive(), [CitationRecall(), Faithfulness()], ctx)
    paras = rec["citation_audit"]["paragraphs"]
    first = next(p for p in paras if p["para_id"] == "sec1-p1")
    assert [c["verdict"] for c in first["claims"]] == ["supported", "inferred"]
    assert first["sentences"] and all("supported" in s for s in first["sentences"])
    json.dumps(rec)                                     # serialisable as saved
    rules = await score_archive(make_archive(), [FactGrounding()], ctx)
    assert "citation_audit" not in rules


def test_table_citations_count_once_per_table():
    from evals.research_eval.citation_audit import CitationAudit, ParagraphAudit

    def pair(row, url, precise, no_claims=False):
        return {"para_id": "t", "sentence": row, "url": url, "claims": 0 if no_claims else 1,
                "no_claims": no_claims, "precise": precise}

    checks = [pair(1, "https://a", True), pair(1, "https://b", False), pair(1, "https://c", False),
              pair(2, "https://a", False), pair(2, "https://b", True), pair(2, "https://c", False)]
    table = ParagraphAudit("t", [], "cited", [], [], table=True, citation_checks=checks)
    cites = CitationAudit([table]).citations
    # 2 rows x 3 URLs would be 6 pairs (2 precise); per table it is 3 URLs, 2 precise.
    assert [(c["url"], c["precise"], c["effective"], c["sentence"]) for c in cites] == [
        ("https://a", True, True, [1, 2]), ("https://b", True, True, [1, 2]),
        ("https://c", False, False, [1, 2])]
    text = ParagraphAudit("p", [], "cited", [], [], citation_checks=checks[:3] + [
        pair(2, "https://d", False, no_claims=True)])
    # Not a table: every pair counts, except the one whose item has no claim.
    assert len(CitationAudit([text]).citations) == 3


def test_supported_claim_needs_a_passage_from_its_own_citations():
    from evals.research_eval.citation_audit import ParagraphAudit, claim_level
    pa = ParagraphAudit("p", [], "cited",
                        [{"text": "A", "urls": ["https://a"]}, {"text": "B", "urls": ["https://b"]}],
                        [{"n": 1, "url": "https://a", "found": True, "passages": [{"id": "1a", "chunk_id": "ca"}]},
                         {"n": 2, "url": "https://b", "found": True, "passages": [{"id": "2a", "chunk_id": "cb"}]}])
    pa.claims = [
        # Backed by A, but it sits in item 2, which cites only B.
        {"claim": "x", "verdict": "supported", "sentences": [2], "chunk_ids": ["ca"]},
        # Spans both items: either citation may back it.
        {"claim": "y", "verdict": "supported", "sentences": [1, 2], "chunk_ids": ["cb"]},
        # No item named: any citation of the paragraph may cover it.
        {"claim": "z", "verdict": "supported", "sentences": [], "chunk_ids": ["ca"]}]
    claim_level(pa)
    assert [(c["claim"], c["supported"], c["units_guessed"]) for c in pa.claim_checks] == [
        ("x", False, False), ("y", True, False), ("z", True, True)]
    assert [(c["sentence"], c["url"], c["precise"]) for c in pa.citation_checks] == [
        (1, "https://a", True), (2, "https://b", True)]


def test_parser_keeps_duplicate_references_for_instruction_following():
    md = "# T\n\n## S\n\nText ([A](https://a.com)).\n\n## References\n\n- [A](https://a.com)\n- [A again](https://a.com)\n"
    parsed = parse_report(md)
    assert parsed["references"] == ["https://a.com"]
    assert parsed["references_listed"] == ["https://a.com", "https://a.com"]
    # A URL written as its own link text is one reference, not two.
    md = "# T\n\n## S\n\nText ([A](https://a.com)).\n\n## References\n\n- [https://a.com](https://a.com)\n- [B](https://b.com)\n"
    assert parse_report(md)["references_listed"] == ["https://a.com", "https://b.com"]


def test_precision_flags_redundant_citations():
    from evals.research_eval.citation_audit import CitationAudit, ParagraphAudit, claim_level
    pa = ParagraphAudit("p", [], "cited",
                        [{"text": "A and B", "urls": ["https://a", "https://b"]}],
                        [{"n": 1, "url": "https://a", "found": True, "passages": [{"id": "1a", "chunk_id": "ca"}]},
                         {"n": 2, "url": "https://b", "found": True, "passages": [{"id": "2a", "chunk_id": "cb"}]}])
    pa.claims = [{"claim": "x", "verdict": "supported", "sentences": [1], "chunk_ids": ["ca", "cb"]},
                 {"claim": "y", "verdict": "supported", "sentences": [1], "chunk_ids": ["ca"]}]
    claim_level(pa)
    from evals.research_eval.metrics.generation.citation import _redundant
    # b only backs x, which a also backs: redundant. a backs y alone: needed.
    assert _redundant(CitationAudit([pa])) == [{"para_id": "p", "sentence": 1, "url": "https://b"}]


def test_analysis_claims_stay_out_of_citation_metrics():
    from evals.research_eval.citation_audit import CitationAudit, ParagraphAudit, claim_level, interpret
    from evals.research_eval.judge import JudgeResponse
    pa = ParagraphAudit("p", [], "cited", [{"text": "A", "urls": ["https://a"]}],
                        [{"n": 1, "url": "https://a", "found": True, "passages": [{"id": "1a", "chunk_id": "ca"}]}])
    pa.response = JudgeResponse({"kind": "factual", "claims": [
        {"claim": "x", "type": "fact", "sentences": [1], "verdict": "supported", "passages": ["1a"]},
        {"claim": "y leads", "type": "analysis", "sentences": [1], "verdict": "inferred", "passages": ["1a"]},
        {"claim": "z", "sentences": [1], "verdict": "unsupported", "passages": []}]},
        "", False, "paragraph_audit", "3")
    interpret(pa)
    assert [c["type"] for c in pa.claims] == ["fact", "analysis", "fact"]   # untyped -> fact
    assert [c["claim"] for c in pa.claim_checks] == ["x", "z"]
    audit = CitationAudit([pa])
    assert len(audit.claim_checks) == 2



async def test_recheck_judges_unsupported_facts_on_checker_picked_passages(ctx):
    ctx.fake.recheck = {"Glencore dominates": {"verdict": "supported", "passages": ["1a"]}}
    audit = await citation_audit(make_archive(), ctx)
    rechecks = [p for p in ctx.fake.prompts if "not fully supported by the material checked" in p]
    # Paragraph 1: only "China refines 65%" (inferred); paragraph 2: both
    # unsupported facts. Uncited paragraphs get no recheck.
    assert len(rechecks) == 2
    second = next(p for p in rechecks if "Glencore" in p)
    assert "1. Glencore dominates\n2. prices triple" in second.split("Material:")[0]
    material = second.split("Material:")[1]
    assert "never-retrieved" not in material
    # The cited page is shown again only for the passage first read as contradicting.
    pa = audit.paragraphs[1]
    assert material.count("recycle.org") == 1 and pa.confirm[0]["url"] == "https://recycle.org/eu"
    assert pa.confirm[0]["n"] > max(s["n"] for s in pa.sources + pa.extra)
    assert re.search(r"Source \[1\] https://(reuters\.com/cobalt|energy\.gov/lithium) passage 1a:", material)
    pa = audit.paragraphs[1]
    glencore = next(c for c in pa.claims if c["claim"] == "Glencore dominates")
    # Citation side unchanged; faithfulness takes the better verdict.
    assert glencore["verdict"] == "contradicted" and glencore["faith_verdict"] == "supported"
    cc = next(c for c in pa.claim_checks if c["claim"] == "Glencore dominates")
    assert cc["supported"] is False and cc["backed_by_uncited"] is True
    assert glencore["elsewhere_chunk_ids"] == [pa.extra[0]["passages"][0]["chunk_id"]]
    # The judge's first call never sees the independent passages.
    first = next(p for p in audit_prompts(ctx) if "Recycling mandates" in p)
    assert "reuters.com" not in first.split("Material:")[1]
    r = await Faithfulness().score(make_archive(), ctx)
    assert r.details["rechecked"] == 3 and r.details["upgraded_by_recheck"] == 1
    rec = await CitationRecall().score(make_archive(), ctx)
    assert rec.details["backed_by_uncited"] == 1


def _pa_with_extra(mode, extra_url, extra_cited):
    from evals.research_eval.citation_audit import ParagraphAudit
    urls = [URL["cobalt"]] if mode == "cited" else []
    pa = ParagraphAudit("p1", [], mode, [{"text": "Glencore is the largest producer.", "urls": urls}],
                        [{"n": 1, "url": URL["cobalt"], "found": True, "cited": mode == "cited",
                          "passages": [{"id": "1a", "chunk_id": "shown"}]}],
                        extra=[{"n": 1, "url": extra_url, "found": True, "cited": extra_cited,
                                "passages": [{"id": "1a", "chunk_id": "unshown"}]}])
    pa.claims = [{"claim": "Glencore is the largest producer", "type": "fact", "verdict": "unsupported",
                  "score": 0.0, "faith_verdict": "unsupported", "faith_score": 0.0,
                  "sentences": [1], "chunk_ids": [], "evidence": ""}]
    return pa


def _recheck(pa, verdict="supported"):
    from evals.research_eval.citation_audit import apply_recheck, claim_level, recheck_todo
    from evals.research_eval.judge import JudgeResponse
    claim_level(pa)
    todo = recheck_todo(pa)
    pa.recheck = JudgeResponse({"claims": [{"claim": 1, "verdict": verdict, "passages": ["1a"]}]},
                               "", False, "claim_recheck", "3")
    apply_recheck(pa, todo)
    return todo


def test_recheck_passage_of_the_cited_page_backs_the_citation():
    # The first call's budget left this passage of the cited page out.
    pa = _pa_with_extra("cited", "https://www.reuters.com/cobalt/", True)
    _recheck(pa)
    cc = pa.claim_checks[0]
    assert cc["supported"] and cc["supported_on_recheck"] and not cc["backed_by_uncited"]
    assert cc["backing_urls"] == [URL["cobalt"]] and pa.citation_checks[0]["precise"]
    assert pa.claims[0]["faith_verdict"] == "supported"


def test_recheck_on_another_page_does_not_back_the_citation():
    pa = _pa_with_extra("cited", URL["lithium"], False)
    _recheck(pa)
    cc = pa.claim_checks[0]
    assert not cc["supported"] and cc["backed_by_uncited"] and not pa.citation_checks[0]["precise"]


def test_uncited_paragraph_facts_are_rechecked_too():
    pa = _pa_with_extra("uncited", URL["lithium"], False)
    todo = _recheck(pa)
    assert len(todo) == 1 and pa.claims[0]["faith_verdict"] == "supported"
    assert pa.claim_checks == []        # nothing cited: no citation checks


async def test_frozen_rubric_replaces_the_rubric_call(tmp_path):
    from evals.research_eval.metrics.generation.writing import Insight
    (tmp_path / "q1.json").write_text(json.dumps({
        "insight": [{"criterion": "causes", "description": "d", "weight": 1}],
        "readability": [{"criterion": "flow", "description": "d", "weight": 1}]}))
    judge = ScriptedJudge()
    cache = EvalCache(":memory:")
    ctx = ScoringContext(cache=cache, judge=Judge(cache, model="judge-x", complete=judge),
                         rubrics_dir=tmp_path)
    r = await Insight().score(make_archive(), ctx)
    assert not any("preparing a grading rubric" in p for p in judge.prompts)
    assert r.details["rubric"]["source"] == "frozen" and r.value == 0.8


async def test_a_contradiction_the_recheck_does_not_confirm_is_unsupported(ctx):
    from evals.research_eval.metrics.generation import ContradictedParagraphs
    ctx.fake.recheck = {}
    audit = await citation_audit(make_archive(), ctx)
    glencore = next(c for c in audit.paragraphs[1].claims if c["claim"] == "Glencore dominates")
    assert glencore["verdict"] == "contradicted" and glencore["faith_verdict"] == "unsupported"
    assert glencore["contradiction_dropped"] is True
    r = await ContradictedParagraphs().score(make_archive(), ctx)
    assert r.details["contradicted"] == 0 and r.details["dropped"][0]["claim"] == "Glencore dominates"


async def test_contradicted_paragraphs_counts_paragraphs_not_claims(ctx):
    from evals.research_eval.metrics.generation import ContradictedParagraphs
    r = await ContradictedParagraphs().score(make_archive(), ctx)
    # Three factual paragraphs; only the recycling one has a contradicted fact.
    assert (r.details["paragraphs"], r.details["contradicted"]) == (3, 1)
    assert r.value == pytest.approx(1 / 3, abs=1e-3) and r.higher_is_better is False
    assert [c["claim"] for c in r.details["flagged"][0]["claims"]] == ["Glencore dominates"]
