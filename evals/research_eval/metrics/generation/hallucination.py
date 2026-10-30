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
_WORD = r"[A-Z][\w&']*(?:-[A-Z][\w&']*)*"
_ENTITY = re.compile(rf"\b{_WORD}(?:\s+(?:of|for|de|the)\s+{_WORD}|\s+{_WORD})*")
_SENT_START = re.compile(r"(^|[.!?:;|]\s+|\n\s*)$")


def fact_tokens(text: str) -> list[tuple[str, str]]:
    """(kind, token) pairs: numbers >= 10 or with decimals, and capitalised names.
    A capitalised first word of a sentence is dropped unless it is an acronym;
    a hyphenated lower-case tail is not part of a name ("EU-wide" -> "EU")."""
    out = []
    norm = _THOUSANDS.sub("", text)
    for m in _NUMBER.finditer(norm):
        tok = m.group(0)
        if "." in tok or int(tok) >= 10:
            out.append(("number", tok))
    for m in _ENTITY.finditer(text):
        tok = m.group(0)
        if _SENT_START.search(text[:m.start()]):
            # Sentence-initial capital says nothing; keep the rest ("Most MiCA" -> "MiCA").
            first, _, rest = tok.partition(" ")
            if not first.isupper() or len(first) < 2:
                tok = rest
        if len(tok) >= 2:
            out.append(("entity", tok))
    return list(dict.fromkeys(out))


def _name_variants(tok: str) -> list[str]:
    """A name as written plus the forms a source may use for the same thing:
    without a leading "the", each word singular or plural ("CASPs" ~ "CASP")."""
    words = tok.split()
    if len(words) > 1 and words[0].lower() == "the":
        words = words[1:]
    out = [" ".join(words).lower()]
    last = words[-1]
    if len(last) > 2 and last.endswith("s"):
        out.append(" ".join(words[:-1] + [last[:-1]]).lower())
    elif last[-1:].isalpha():
        out.append(" ".join(words[:-1] + [last + "s"]).lower())
    return out


def _acronym(tok: str) -> str | None:
    """"Digital Operational Resilience Act" -> "DORA"; "Transfer of Funds Regulation" -> "TFR"."""
    caps = [w for w in tok.split() if w[:1].isupper()]
    return "".join(w[0] for w in caps) if len(caps) >= 3 else None


def found_in(kind: str, tok: str, evidence: str, evidence_lower: str) -> bool:
    if kind == "number":
        return re.search(rf"(?<![\d.]){re.escape(tok)}(?!\.?\d)", evidence) is not None
    if any(v in evidence_lower for v in _name_variants(tok)):
        return True
    acro = _acronym(tok)
    return acro is not None and re.search(rf"\b{acro}s?\b", evidence) is not None


class FactGrounding(Metric):
    """Rule check: figures and names in a paragraph appear verbatim in what it cites.

        value = tokens found in the cited chunks / tokens checked

    Only paragraphs that cite at least one retrieved URL; the evidence is every
    chunk of those URLs. Tokens: numbers (thousands separators ignored; 45 does
    not match 45.3) and capitalised names (case-insensitive phrase match; singular
    and plural forms match, a leading "the" is ignored, and a name of three or
    more capitalised words also matches its acronym, "Digital Operational
    Resilience Act" ~ "DORA"). `details` reports numbers and names separately.
    Citation anchor text, i.e. the source's own name, is not checked.
    Unjudged and uncalibrated: a paraphrased or converted figure counts as missing.
    """

    name, category = "fact_grounding", "generation.hallucination"
    version = "2"

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        paras = [p for p in audited_paragraphs(archive)
                 if any(normalize_url(c["url"]) in archive.chunks_by_url for c in p["citations"])]
        if not paras:
            return self.skip("no paragraph cites a retrieved source")
        per_para, found, total = [], 0, 0
        by_kind = {"number": [0, 0], "entity": [0, 0]}      # [found, checked]
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
            missing = []
            for k, t in toks:
                ok = found_in(k, t, evidence, ev_lower)
                by_kind[k][0] += ok
                by_kind[k][1] += 1
                if not ok:
                    missing.append(t)
            found += len(toks) - len(missing)
            total += len(toks)
            if toks:
                per_para.append({"para_id": p["para_id"], "checked": len(toks), "missing": missing})
        if not total:
            return self.skip("no numbers or names to check")
        return self.result(rounded(found / total), checked=total, found=found,
                           numbers={"checked": by_kind["number"][1], "found": by_kind["number"][0]},
                           names={"checked": by_kind["entity"][1], "found": by_kind["entity"][0]},
                           paragraphs=len(per_para), per_paragraph=per_para)
