"""
B. Citations: ALCE citation recall / precision, citation coverage, effective
citations (eval-design/generation-metrics.md §3.1). The judged ones read the
shared citation audit (one judge call per paragraph, see citation_audit.py).
"""

from __future__ import annotations

from collections import Counter

from ...archive import RunArchive, normalize_url
from ...citation_audit import AUDIT_VERSION, CitationAudit, citation_audit
from ...prompts import PARAGRAPH_AUDIT
from ...report_parser import body_paragraphs, cited_urls
from ..base import Metric, MetricResult, ScoringContext, rounded
from .common import body_word_count
from ..lexical import idf_table, symmetric_overlap


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
    """Citation recall per claim: cited claims that their own citations support.

        value = supported cited claims / cited claims

    Claims come from the citation audit (the judge splits each paragraph into
    claims; one claim may span several sentences). A claim is cited when an
    item it comes from cites a source, and supported when its verdict is
    "supported" (strict: inferences do not count) and a passage it rests on
    belongs to one of those cited URLs (`citation_audit.claim_level`). Claims
    in uncited paragraphs or after a paragraph's last citation are left to
    faithfulness. `details.unit_level` keeps the former ALCE per-citing-unit
    value, where one unsupported claim failed a whole paragraph-long unit.
    """

    name = "citation_recall"
    version = f"2.audit{AUDIT_VERSION}"     # 2: claim citation share in details

    def from_audit(self, audit, archive):
        claims = audit.claim_checks
        if not claims:
            return self.skip("no cited claims")
        ok = sum(c["supported"] for c in claims)
        factual = sum(len(p.claims) for p in audit.judged if p.kind == "factual")
        units = [s for s in audit.sentence_checks if s["judged"]]
        unit_ok = sum(s["supported"] for s in units)
        return self.result(rounded(ok / len(claims)), cited_claims=len(claims), supported=ok,
                           factual_claims=factual,
                           cited_share=rounded(len(claims) / factual) if factual else None,
                           supported_of_all_claims=rounded(ok / factual) if factual else None,
                           verdicts=dict(Counter(c["verdict"] for c in claims)),
                           supported_elsewhere=sum(c["verdict"] == "supported" and not c["backing_urls"]
                                                   for c in claims),
                           unit_level=rounded(unit_ok / len(units)) if units else None,
                           unsupported=[{k: c[k] for k in ("para_id", "claim", "verdict", "urls")}
                                        for c in claims if not c["supported"]])


class CitationPrecision(_AuditMetric):
    """Citation precision per claim: citations that back a claim of their item.

        value = precise citations / citations   (citation = one item-URL pair;
                                                 in a table, one table-URL pair)

    Precise: the URL holds a passage that a "supported" claim of the same item
    rests on. Citations of items without any factual claim are not counted.
    A URL that was never retrieved can back nothing. `details.unit_level`
    keeps the former ALCE value.
    """

    name = "citation_precision"
    version = f"2.audit{AUDIT_VERSION}"     # 2: redundant citations in details

    def from_audit(self, audit, archive):
        cites = audit.citations
        if not cites:
            return self.skip("no citations of factual claims")
        precise = sum(c["precise"] for c in cites)
        old = audit.unit_citations
        redundant = _redundant(audit)
        return self.result(rounded(precise / len(cites)), citations=len(cites), precise=precise,
                           unit_level=rounded(sum(c["precise"] for c in old) / len(old)) if old else None,
                           redundant=len(redundant), redundant_rate=rounded(len(redundant) / len(cites)),
                           redundant_citations=redundant,
                           imprecise=[{k: c[k] for k in ("para_id", "sentence", "url")}
                                      for c in cites if not c["precise"]])


def _redundant(audit: CitationAudit) -> list[dict]:
    """Precise citations that add nothing: every supported claim they back is
    also backed by another URL of the same item (the claim-level form of
    ALCE's "the rest suffice"). Corroboration, not an error, so it is shown
    beside precision rather than taken out of it."""
    out = []
    for p in audit.judged:
        for c in p.citation_checks:
            if not c["precise"]:
                continue
            backed = [cc for cc in p.claim_checks if cc["supported"] and c["sentence"] in cc["units"]
                      and c["url"] in cc["backing_urls"]]
            if backed and all(len(cc["backing_urls"]) > 1 for cc in backed):
                out.append({"para_id": p.para_id, "sentence": c["sentence"], "url": c["url"]})
    return out


class EffectiveCitations(_AuditMetric):
    """Number of distinct pieces of evidence the report cites correctly.

        value = distinct retrieved chunks that a "supported" cited claim rests
                on through its own citations, near-duplicates merged

    Evidence, not pages or citation pairs: a page cited correctly in ten
    paragraphs for the same passage counts once, and two passages of one page
    backing different claims count twice. Near-duplicate chunks (syndicated
    copies of the same text on different sites; BM25-weighted symmetric
    overlap >= `DUPLICATE`) are merged, by rule, with no judge call.
    `details` keeps the citation-pair count and the distinct URL count.
    """

    name = "effective_citations"
    version = f"3.audit{AUDIT_VERSION}"     # 2: distinct evidence chunks; 3: per 1k words
    DUPLICATE = 0.8

    def from_audit(self, audit, archive):
        cites = audit.citations
        if not cites:
            return self.skip("no citations of factual claims")
        eff = [c for c in cites if c["effective"]]
        chunks = list(dict.fromkeys(cid for c in audit.claim_checks if c["supported"]
                                    for cid in c["backing_chunks"] if cid in archive.chunks))
        idf = idf_table([archive.chunks[c]["content"] for c in archive.retrieved_chunk_ids])
        groups: list[str] = []          # one representative chunk per piece of evidence
        for cid in chunks:
            text = archive.chunks[cid]["content"]
            if not any(symmetric_overlap(text, archive.chunks[g]["content"], idf) >= self.DUPLICATE
                       for g in groups):
                groups.append(cid)
        words = body_word_count(archive)
        return self.result(float(len(groups)), evidence_chunks=len(chunks),
                           words=words, per_1k_words=rounded(1000 * len(groups) / words) if words else None,
                           merged_duplicates=len(chunks) - len(groups),
                           effective_pairs=len(eff), citations=len(cites),
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
