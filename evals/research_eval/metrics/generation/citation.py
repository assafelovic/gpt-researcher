"""
B. Citations: ALCE citation recall / precision, citation coverage, effective
citations (eval-design/generation-metrics.md §3.1). The judged ones read the
shared citation audit (one judge call per paragraph, see citation_audit.py).
"""

from __future__ import annotations

from ...archive import RunArchive, normalize_url
from ...citation_audit import AUDIT_VERSION, CitationAudit, citation_audit
from ...prompts import PARAGRAPH_AUDIT
from ...report_parser import body_paragraphs, cited_urls
from ..base import Metric, MetricResult, ScoringContext, rounded


class _AuditMetric(Metric):
    category = "generation.citation"
    version = f"1.audit{AUDIT_VERSION}"
    uses_llm = True
    prompts = (PARAGRAPH_AUDIT,)

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self.skip("no judge configured")
        if not body_paragraphs(archive.report):
            return self.skip("empty report")
        audit = await citation_audit(archive, ctx)
        failed = [p.para_id for p in audit.paragraphs if p.error]
        if failed and not audit.judged:
            # Otherwise the skip reason would read "no citations" for a report full of them.
            res = self.skip("every judge call failed", failed_paragraphs=failed)
        else:
            res = self.from_audit(audit, archive)
        if failed:
            res.details["failed_paragraphs"] = failed
        # Every audit metric reports the same shared calls; count them once.
        res.llm = {**self.llm_record(ctx, audit.responses), "shared": "citation_audit"}
        return res

    def from_audit(self, audit: CitationAudit, archive: RunArchive) -> MetricResult:
        raise NotImplementedError


class CitationRecall(_AuditMetric):
    """ALCE citation recall: citing sentences fully supported by their own sources.

        value = supported citing sentences / judged citing sentences

    Sentences without a citation are not in the denominator (they are covered
    by faithfulness). A sentence whose sources were never retrieved counts as
    unsupported without asking the judge.
    """

    name = "citation_recall"

    def from_audit(self, audit, archive):
        sents = [s for s in audit.sentence_checks if s["judged"]]
        if not sents:
            return self.skip("no citing sentences")
        ok = sum(s["supported"] for s in sents)
        return self.result(rounded(ok / len(sents)), citing_sentences=len(sents), supported=ok,
                           unsupported=[{k: s[k] for k in ("para_id", "sentence", "text")}
                                        | {"urls": [c["url"] for c in s["citations"]]}
                                        for s in sents if not s["supported"]])


class CitationPrecision(_AuditMetric):
    """ALCE citation precision, as in its reference implementation.

        value = precise citations / citations   (citation = one sentence-URL pair)

    Irrelevant citation: does not support its sentence alone, and the sentence's
    other citations support it without it. As in ALCE, citations of a sentence
    that is not supported at all count as imprecise, so precision also drops
    with recall; `details.over_citations` counts only the irrelevant ones.
    """

    name = "citation_precision"

    def from_audit(self, audit, archive):
        cites = [(s, c) for s in audit.sentence_checks if s["judged"] for c in s["citations"]]
        if not cites:
            return self.skip("no citations")
        precise = sum(c["precise"] for _, c in cites)
        over = [{"para_id": s["para_id"], "sentence": s["sentence"], "url": c["url"]}
                for s, c in cites if s["supported"] and not c["precise"]]
        return self.result(rounded(precise / len(cites)), citations=len(cites), precise=precise,
                           over_citations=len(over), irrelevant=over)


class EffectiveCitations(_AuditMetric):
    """Number of citations backed by their source (DeepResearch Bench FACT style).

        value = sentence-URL citations whose source supports the sentence
                (alone, or as the only citation of a supported sentence)

    A count, not a ratio: a report with three correct citations scores 100% on
    the ratios but much lower here than one with forty.
    """

    name = "effective_citations"

    def from_audit(self, audit, archive):
        cites = [c for s in audit.sentence_checks if s["judged"] for c in s["citations"]]
        if not cites:
            return self.skip("no citations")
        eff = [c for c in cites if c["effective"]]
        return self.result(float(len(eff)), citations=len(cites),
                           effective_urls=len({normalize_url(c["url"]) for c in eff}))


class CitationCoverage(Metric):
    """Share of the reference list that the body actually cites (rule-based, URL level).

        value = references cited in the body / references

    The references section is the report's claim about its sources; this is how
    much of that claim the body backs with in-text citations. Formerly
    `citation_faithfulness`, which compared domains.
    """

    name, category = "citation_coverage", "generation.citation"

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        parsed = archive.report
        refs = list(dict.fromkeys(normalize_url(u) for u in parsed["references"]))
        if not refs:
            return self.skip("no references section with links")
        body = {normalize_url(u) for u in cited_urls(parsed)}
        hit = [u for u in refs if u in body]
        return self.result(rounded(len(hit) / len(refs)), references=len(refs),
                           cited_in_body=len(hit),
                           references_not_cited=[u for u in refs if u not in body],
                           body_not_in_references=sorted(body - set(refs)))
