"""
C. Hallucination (eval-design/generation-metrics.md §3.2): judged faithfulness
of every factual claim, and a rule check that figures and names in a paragraph
appear in the sources it cites. Listed separately; there is no combined score.
"""

from __future__ import annotations

import re
from collections import Counter

from ...archive import RunArchive, normalize_url
from ...citation_audit import VERDICT_SCORES, CitationAudit, audited_paragraphs
from ..base import Metric, MetricResult, ScoringContext, rounded
from .citation import _AuditMetric


class Faithfulness(_AuditMetric):
    """Mean verdict score of the report's factual claims, in [-1, 1].

    Claims are extracted per paragraph by the judge (not taken as the cited
    sentences), and checked against the paragraph's cited passages; paragraphs
    with no citations are checked against the BM25 top passages of everything
    retrieved, and skipped when the judge finds them non-factual.

        supported 1 | inferred 0.5 / 0.4 / 0.3 | unsupported 0 | contradicted -1

    Known gap: a claim citing A but backed by B in the same paragraph passes
    here; citation recall / precision catch it.
    """

    name, category = "faithfulness", "generation.hallucination"

    def from_audit(self, audit: CitationAudit, archive: RunArchive) -> MetricResult:
        claims = [(p, c) for p in audit.judged for c in p.claims]
        scored = [c["score"] for _, c in claims if c["score"] is not None]
        if not scored:
            return self.skip("no factual claims judged")
        verdicts = Counter(c["verdict"] for _, c in claims)
        per_para = []
        for p in audit.judged:
            s = [c["score"] for c in p.claims if c["score"] is not None]
            per_para.append({"para_id": p.para_id, "mode": p.mode, "kind": p.kind,
                             "claims": len(p.claims), "score": rounded(sum(s) / len(s)) if s else None})
        flagged = [{"para_id": p.para_id, "mode": p.mode, **{k: c[k] for k in ("claim", "verdict", "evidence")}}
                   for p, c in claims if (c["score"] if c["score"] is not None else 0) <= 0]
        return self.result(rounded(sum(scored) / len(scored)), claims=len(scored),
                           verdicts=dict(verdicts),
                           unknown_verdicts=len(claims) - len(scored),
                           uncited_factual_paragraphs=sum(p.mode == "uncited" and p.kind == "factual"
                                                          for p in audit.judged),
                           flagged=flagged, per_paragraph=per_para,
                           verdict_scores=VERDICT_SCORES)


_NUMBER = re.compile(r"(?<![\w.])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.,])\d+(?:\.\d+)?")
_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}\b)")
_ENTITY = re.compile(r"\b(?:[A-Z][\w&'\-]*|[A-Z]{2,})(?:\s+(?:of|for|and|de|the)\s+[A-Z][\w&'\-]*|\s+[A-Z][\w&'\-]*)*")
_SENT_START = re.compile(r"(^|[.!?:;]\s+|\n)$")


def fact_tokens(text: str) -> list[tuple[str, str]]:
    """(kind, token) pairs: numbers >= 10 or with decimals, and capitalised names
    not at a sentence start (single capitalised words at a start are skipped)."""
    out = []
    norm = _THOUSANDS.sub("", text)
    for m in _NUMBER.finditer(norm):
        tok = m.group(0)
        if "." in tok or int(tok) >= 10:
            out.append(("number", tok))
    for m in _ENTITY.finditer(text):
        tok = m.group(0)
        at_start = bool(_SENT_START.search(text[:m.start()]))
        if at_start and " " not in tok and not tok.isupper():
            continue
        if len(tok) >= 2:
            out.append(("entity", tok))
    return list(dict.fromkeys(out))


def found_in(kind: str, tok: str, evidence: str, evidence_lower: str) -> bool:
    if kind == "number":
        return re.search(rf"(?<![\d.]){re.escape(tok)}(?!\.?\d)", evidence) is not None
    return " ".join(tok.lower().split()) in evidence_lower


class FactGrounding(Metric):
    """Rule check: figures and names in a paragraph appear verbatim in what it cites.

        value = tokens found in the cited chunks / tokens checked

    Only paragraphs that cite at least one retrieved URL; the evidence is every
    chunk of those URLs. Tokens: numbers (thousands separators ignored; 45 does
    not match 45.3) and capitalised names (case-insensitive phrase match).
    Citation anchor text, i.e. the source's own name, is not checked.
    Unjudged and uncalibrated: a paraphrased or converted figure counts as missing.
    """

    name, category = "fact_grounding", "generation.hallucination"

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        paras = [p for p in audited_paragraphs(archive)
                 if any(normalize_url(c["url"]) in archive.chunks_by_url for c in p["citations"])]
        if not paras:
            return self.skip("no paragraph cites a retrieved source")
        per_para, found, total = [], 0, 0
        for p in paras:
            cids = [cid for c in p["citations"]
                    for cid in archive.chunks_by_url.get(normalize_url(c["url"]), [])]
            evidence = _THOUSANDS.sub("", "\n".join(archive.chunks[c]["content"] for c in cids))
            ev_lower = " ".join(evidence.lower().split())
            text = p["text"]
            for c in p["citations"]:
                if c["anchor"]:
                    text = text.replace(c["anchor"], " ")
            text = re.sub(r"https?://\S+", " ", text)
            toks = fact_tokens(text)
            missing = [t for k, t in toks if not found_in(k, t, evidence, ev_lower)]
            found += len(toks) - len(missing)
            total += len(toks)
            if toks:
                per_para.append({"para_id": p["para_id"], "checked": len(toks), "missing": missing})
        if not total:
            return self.skip("no numbers or names to check")
        return self.result(rounded(found / total), checked=total, found=found,
                           paragraphs=len(per_para), per_paragraph=per_para)
