"""
B. Source metrics: what the retrieval brought back.

Both score the distinct URLs of the chunks that reached the context, i.e. the
material the writer could actually read. Logic copied from
evals/quality_eval/metrics.py (source_authority / source_diversity) rather than
imported, so the old module can be deleted later without touching this one.
"""

from __future__ import annotations

import math
from collections import Counter
from urllib.parse import urlparse

from ...archive import RunArchive
from ...cache import stable_hash
from ...prompts import DOMAIN_AUTHORITY
from ...report_parser import body_paragraphs
from ..base import Metric, MetricResult, ScoringContext, rounded


def domain_of(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


class SourceDiversity(Metric):
    """diversity_ratio = distinct domains / sources; domain_entropy = -Σ p·log2 p."""

    name, category = "source_diversity", "retrieval.source"

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        domains = [domain_of(u) for u in archive.retrieved_urls]
        domains = [d for d in domains if d]
        if not domains:
            return self.skip("no retrieved sources")
        counts = Counter(domains)
        total = len(domains)
        entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
        return self.result(rounded(len(counts) / total),
                           total_sources=total, unique_domains=len(counts),
                           diversity_ratio=rounded(len(counts) / total),
                           domain_entropy=rounded(entropy),
                           top_domains=counts.most_common(5))


_HIGH_AUTHORITY_DOMAINS = {
    "nature.com", "science.org", "cell.com", "thelancet.com",
    "nejm.org", "pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov",
    "arxiv.org", "scholar.google.com", "jstor.org", "ssrn.com",
    "plos.org", "biorxiv.org", "medrxiv.org",
    "who.int", "un.org", "imf.org", "worldbank.org",
    "oecd.org", "wto.org", "europa.eu",
    "britannica.com",
}

_MAJOR_NEWS_DOMAINS = {
    "bbc.com", "bbc.co.uk", "reuters.com", "apnews.com",
    "nytimes.com", "theguardian.com", "washingtonpost.com",
    "wsj.com", "economist.com", "ft.com", "bloomberg.com",
    "npr.org", "pbs.org", "aljazeera.com",
}


def rule_score(domain: str) -> tuple[float, str] | None:
    """High-confidence rule tiers; None defers the domain to the judge."""
    d = domain.lower().removeprefix("www.")
    if d.endswith(".gov"):           return 1.0, "government"
    if d.endswith(".edu"):           return 0.9, "academic-edu"
    if any(d == h or d.endswith("." + h) for h in _HIGH_AUTHORITY_DOMAINS):
        return 0.9, "high-authority"
    if any(d == h or d.endswith("." + h) for h in _MAJOR_NEWS_DOMAINS):
        return 0.8, "major-news"
    if "wikipedia.org" in d:         return 0.75, "wikipedia"
    return None


def fallback_score(domain: str) -> tuple[float, str]:
    """Rule-only score for deferred domains the judge did not (or could not) score."""
    d = domain.lower().removeprefix("www.")
    if d.endswith(".org"): return 0.65, "nonprofit-org"
    if d.endswith(".com"): return 0.5, "commercial"
    return 0.4, "unknown"


class SourceAuthority(Metric):
    """Authority (0-1) of the sources the report rests on.

        value = mean domain score over the report's citations, one per
                paragraph-URL pair, so a source cited in ten paragraphs weighs
                ten times one cited once

    The mean over every retrieved source is kept in `details.retrieved_mean`:
    a run that searches widely and then cites regulators would otherwise score
    below a run that retrieves and cites ten vendor blogs. A report with no
    citations falls back to the retrieved mean (`details.basis`).

    Rule tiers first. Deferred domains are looked up in the global domain
    cache (domain + prompt version), and the rest are scored in ONE batched
    judge call whose verdicts are cached per domain, so the cost per run
    falls towards zero as the cache fills. Without a judge, or for domains the
    judge skipped, the rule fallback (.org 0.65 / .com 0.5 / other 0.4) is used
    and the domains are listed in `fallback_domains`.
    """

    name, category = "source_authority", "retrieval.source"
    version = "2"
    uses_llm = True
    prompts = (DOMAIN_AUTHORITY,)

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        domains = [d for d in (domain_of(u) for u in archive.retrieved_urls) if d]
        cited = [d for d in (domain_of(c["url"]) for p in body_paragraphs(archive.report)
                             for c in p["citations"]) if d]
        if not domains and not cited:
            return self.skip("no retrieved sources")

        verdicts: dict[str, dict] = {}
        deferred = []
        for d in sorted(set(domains) | set(cited)):
            rule = rule_score(d)
            if rule is not None:
                verdicts[d] = {"score": rule[0], "tier": rule[1], "basis": "rule"}
                continue
            cached = ctx.cache.get("domain", stable_hash(d, DOMAIN_AUTHORITY.version))
            if cached is not None:
                verdicts[d] = {**cached, "basis": "domain_cache"}
            else:
                deferred.append(d)

        responses = []
        if deferred and ctx.judge is not None:
            r = await ctx.judge.ask(DOMAIN_AUTHORITY.id, DOMAIN_AUTHORITY.version,
                                    DOMAIN_AUTHORITY.render(domains="\n".join(f"- {d}" for d in deferred)))
            responses.append(r)
            if r.error is not None or not isinstance(r.parsed, list):
                # A failed call must not turn into fallback scores that look like a real result.
                res = self.skip("judge call failed", n_sources=len(domains),
                                unscored_domains=deferred, error=r.error, raw=r.raw[:500])
                res.llm = self.llm_record(ctx, responses)
                return res
            for item in r.parsed:
                try:
                    d = str(item["domain"]).lower().removeprefix("www.")
                    v = {"score": max(0.0, min(1.0, float(item["score"]))),
                         "tier": f"llm:{item.get('reason', '')}", "judge_model": ctx.judge.model}
                except (KeyError, TypeError, ValueError):
                    continue
                if d in deferred:
                    ctx.cache.put("domain", stable_hash(d, DOMAIN_AUTHORITY.version), v)
                    verdicts[d] = {**v, "basis": "judge"}

        fallback = []
        for d in deferred:
            if d not in verdicts:
                s, tier = fallback_score(d)
                verdicts[d] = {"score": s, "tier": tier, "basis": "fallback"}
                fallback.append(d)

        def mean(ds):
            return rounded(sum(verdicts[d]["score"] for d in ds) / len(ds)) if ds else None

        res = self.result(mean(cited) if cited else mean(domains),
                          basis="citations" if cited else "retrieved",
                          n_citations=len(cited), retrieved_mean=mean(domains),
                          n_sources=len(domains),
                          cited_domains=Counter(cited).most_common(),
                          breakdown=sorted(({"domain": d, **v} for d, v in verdicts.items()),
                                           key=lambda x: -x["score"]),
                          fallback_domains=fallback)
        res.llm = self.llm_record(ctx, responses)
        return res
