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


def concentration(domains: list[str]) -> dict:
    """How spread a list of domains is (one entry per source or citation).

    p_i = share of domain i.
      hhi              Σ p_i², the Herfindahl-Hirschman index: 1 = one domain, 1/n = n even
      effective        1 / hhi, the inverse Simpson index: as many domains as
                       this many equally used ones
      gini_simpson     1 - hhi: chance two random entries come from different domains
      entropy          -Σ p_i·log2 p_i (Shannon, bits)
      evenness         entropy / log2(domains), Pielou: 1 = perfectly even
    """
    counts = Counter(domains)
    total = len(domains)
    shares = [c / total for c in counts.values()]
    hhi = sum(p * p for p in shares)
    entropy = -sum(p * math.log2(p) for p in shares)
    return {"n": total, "domains": len(counts), "hhi": rounded(hhi),
            "effective": rounded(1 / hhi), "gini_simpson": rounded(1 - hhi),
            "entropy": rounded(entropy),
            "evenness": rounded(entropy / math.log2(len(counts))) if len(counts) > 1 else None,
            "top_domains": counts.most_common(5)}


class SourceDiversity(Metric):
    """Normalised Shannon entropy of the domains the report body cites.

        p_i   = share of body citations (one per paragraph-URL pair) from domain i
        H     = -Σ p_i·log2 p_i
        value = H / log2(n citations)

    The divisor is the most entropy n citations can have (each from its own
    domain), so a report leaning on one or two sites scores low however even
    their split, while concentrating on several sites is only mildly
    penalised. `details.evenness` is Pielou's H / log2(domains). With no body
    citations the retrieved sources are used (`details.basis`). Both
    distributions' measures are in `details.cited` / `details.retrieved`
    (`concentration`); `diversity_ratio` = distinct retrieved domains /
    retrieved sources was the v1 value.
    """

    name, category = "source_diversity", "retrieval.source"
    version = "3"           # 3: normalised entropy of cited domains

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        retrieved = [d for d in (domain_of(u) for u in archive.retrieved_urls) if d]
        cited = [d for d in (domain_of(c["url"]) for p in body_paragraphs(archive.report)
                             for c in p["citations"]) if d]
        if not retrieved and not cited:
            return self.skip("no sources")
        basis, domains = ("cited", cited) if cited else ("retrieved", retrieved)
        c = concentration(domains)
        value = 0.0 if len(domains) < 2 else c["entropy"] / math.log2(len(domains))
        rc = concentration(retrieved) if retrieved else None
        return self.result(rounded(value), basis=basis, entropy=c["entropy"],
                           evenness=c["evenness"], n=len(domains), domains=c["domains"],
                           cited=concentration(cited) if cited else None, retrieved=rc,
                           diversity_ratio=rounded(rc["domains"] / rc["n"]) if rc else None)


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
