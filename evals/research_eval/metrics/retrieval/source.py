"""
B. Source metrics: what the retrieval brought back.

Both score the distinct URLs of the chunks that reached the context, i.e. the
material the writer could actually read. Logic copied from
evals/quality_eval/metrics.py (source_authority / source_diversity) rather than
imported, so the old module can be deleted later without touching this one.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime, timezone
from string import ascii_lowercase
from urllib.parse import urlparse

from gpt_researcher.context.lexical import tokenize

from ...archive import RunArchive, normalize_url
from ...cache import stable_hash
from ...key_points import get_key_points
from ...prompts import DOMAIN_AUTHORITY, KEY_POINTS, MATERIAL_COVERAGE
from ...report_parser import body_paragraphs, cited_urls
from ..base import Metric, MetricResult, ScoringContext, rounded
from ..lexical import idf_table, weighted_overlap


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
      pie              n/(n-1) * (1 - hhi), Hurlbert's PIE: chance that two
                       entries drawn without replacement are from different
                       domains (Gini-Simpson without its small-sample bias)
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
            "pie": rounded(total / (total - 1) * (1 - hhi)) if total > 1 else None,
            "top_domains": counts.most_common(5)}


class SourceDiversity(Metric):
    """Gini-Simpson diversity of the domains the report body cites, with
    Hurlbert's small-sample correction (PIE), in [0, 1]: the chance that two
    citations picked at random (without replacement) come from different
    domains.

        n     = body citations (one per paragraph-URL pair)
        p_i   = share of them from domain i
        value = n/(n-1) * (1 - Σ p_i²)        (1 - Σ p_i² is Gini-Simpson)

    0 = every citation is from one domain, or the body cites nothing; 1 = no
    two citations share a domain; citing two domains half and half gives
    about 0.5. It is an
    unbiased estimate, so citing more of the same mix does not by itself raise
    it (entropy and the domain count do rise as more rare domains turn up);
    a report that draws on more domains still scores higher, and on v12
    reports it still correlates with length (r = 0.83 against word count,
    entropy 0.93), largely because detailed reports cite more domains. Unlike
    Pielou evenness, it does not give full marks to a report that cites two
    domains evenly. A report whose body cites nothing scores 0 (the v4 value
    fell back to the retrieved sources, so an uncited report scored about 1);
    the retrieved sources' spread stays in `details.retrieved`.
    `details.entropy` (bits) was the v3 value; 2^H
    (`equivalent_domains`), evenness, HHI and the domain count are beside it,
    for citations and retrieved sources (`cited` / `retrieved`);
    `diversity_ratio` = distinct retrieved domains / retrieved sources was v1.
    """

    name, category = "source_diversity", "retrieval.source"
    version = "5"           # 3: entropy; 4: Gini-Simpson (Hurlbert's PIE); 5: no citations = 0, no fallback

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        retrieved = [d for d in (domain_of(u) for u in archive.retrieved_urls) if d]
        cited = [d for d in (domain_of(c["url"]) for p in body_paragraphs(archive.report)
                             for c in p["citations"]) if d]
        if not retrieved and not cited:
            return self.skip("no sources")
        rc = concentration(retrieved) if retrieved else None
        ratio = rounded(rc["domains"] / rc["n"]) if rc else None
        if not cited:
            # Nothing cited: the report rests on no source, so it spreads over none.
            return self.result(0.0, basis="no body citations", n=0, cited=None, retrieved=rc,
                               diversity_ratio=ratio)
        c = concentration(cited)
        # One citation: nothing to spread over, so no diversity.
        return self.result(c["pie"] if c["pie"] is not None else 0.0, basis="cited", entropy=c["entropy"],
                           equivalent_domains=rounded(2 ** c["entropy"]),
                           evenness=c["evenness"], n=len(cited), domains=c["domains"],
                           cited=c, retrieved=rc, diversity_ratio=ratio)


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
    below a run that retrieves and cites ten vendor blogs. A report whose body
    cites nothing is skipped (it rests on no source to rate; citation recall
    and coverage already score it 0); v2 fell back to the retrieved mean,
    which gave an uncited report an ordinary-looking value.

    Rule tiers first. Deferred domains are looked up in the global domain
    cache (domain + prompt version), and the rest are scored in ONE batched
    judge call whose verdicts are cached per domain, so the cost per run
    falls towards zero as the cache fills. Without a judge, or for domains the
    judge skipped, the rule fallback (.org 0.65 / .com 0.5 / other 0.4) is used
    and the domains are listed in `fallback_domains`.
    """

    name, category = "source_authority", "retrieval.source"
    version = "3"           # 3: no fallback to retrieved sources when nothing is cited
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

        if not cited:
            res = self.skip("no body citations", n_citations=0, retrieved_mean=mean(domains),
                            n_sources=len(domains), fallback_domains=fallback)
            res.llm = self.llm_record(ctx, responses)
            return res
        res = self.result(mean(cited), basis="citations",
                          n_citations=len(cited), retrieved_mean=mean(domains),
                          n_sources=len(domains),
                          cited_domains=Counter(cited).most_common(),
                          breakdown=sorted(({"domain": d, **v} for d, v in verdicts.items()),
                                           key=lambda x: -x["score"]),
                          fallback_domains=fallback)
        res.llm = self.llm_record(ctx, responses)
        return res


_YEAR = re.compile(r"(?<![\d.,/-])(19[89]\d|20\d\d)(?![\d,])")
_URL_DATE = re.compile(r"(?<!\d)(20\d\d)[/_-]?(0[1-9]|1[0-2])(?:[/_-]?(0[1-9]|[12]\d|3[01]))?(?!\d)")
_URL_YEAR = re.compile(r"/(19[89]\d|20\d\d)/")


def run_year(archive: RunArchive) -> int:
    started = str(archive.meta.get("started_at") or "")
    return int(started[:4]) if started[:4].isdigit() else datetime.now(timezone.utc).year


def source_year(url: str, title: str, text: str, now: int) -> tuple[int | None, str]:
    """(year, basis): when a source's information dates from, by rule.

    A date in the URL path ("/2025/03/", "2025-03-14") is taken as the
    publication date. Otherwise the latest year named in the title or the
    retrieved text, ignoring years after the run (forecasts: "by 2030").
    """
    path = urlparse(url).path
    years = [int(m.group(1)) for m in _URL_DATE.finditer(path)] + \
            [int(y) for y in _URL_YEAR.findall(path)]
    years = [y for y in years if y <= now]
    if years:
        return max(years), "url"
    named = [int(y) for y in _YEAR.findall(f"{title}\n{text}") if int(y) <= now]
    return (max(named), "text") if named else (None, "none")


class SourceRecency(Metric):
    """Share of the report's cited sources whose information is recent:
    dated in the run's year or the `recency_years` (default 1) before it.

        value = recent cited sources / dated cited sources   (distinct URLs)

    A rule, with no search and no judge: the date is the one in the URL path
    when there is one (a publication date), otherwise the latest year named in
    the source's title or retrieved text, years after the run left out (a
    forecast "by 2030" does not make a page new). This dates the sources, not
    each fact: a 2026 article can still quote 2021 figures. Sources with no
    year are left out of the value (unknown is not old) and counted in
    `details.undated`. `details.retrieved_share` is the same share over every
    source that reached the writer, to compare what the report cited with what
    retrieval offered; `per_citation` weights each source by its body citations.
    Meant for time-sensitive questions (all of questions_v0 are); for a
    question about settled history an old source is no defect.
    """

    name, category = "source_recency", "retrieval.source"
    version = "1"
    YEARS = 1

    def _dates(self, archive: RunArchive, urls: list[str], now: int) -> dict[str, tuple[int | None, str]]:
        out = {}
        for u in urls:
            cids = archive.chunks_by_url.get(normalize_url(u), [])
            title = next((archive.chunks[c].get("title") or "" for c in cids), "")
            text = "\n".join(archive.chunks[c]["content"] for c in cids)
            out[u] = source_year(u, title, text, now)
        return out

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        now = run_year(archive)
        cutoff = now - int(ctx.option("recency_years", self.YEARS))
        cited = [u for u in cited_urls(archive.report) if normalize_url(u) in archive.chunks_by_url]
        if not cited:
            return self.skip("no body citations of retrieved sources", run_year=now)
        dates = self._dates(archive, cited, now)
        dated = {u: y for u, (y, _) in dates.items() if y is not None}
        offered = list(dict.fromkeys(archive.chunks[c]["url"] for c in archive.writer_chunk_ids
                                     if archive.chunks[c].get("url")))
        offered_years = [y for y, _ in self._dates(archive, offered, now).values() if y is not None]
        n_cites = Counter(normalize_url(c["url"]) for p in body_paragraphs(archive.report)
                          for c in p["citations"])
        weights = {u: n_cites[normalize_url(u)] for u in dated}
        details = dict(
            run_year=now, cutoff=cutoff, cited=len(cited), dated=len(dated),
            undated=len(cited) - len(dated),
            basis=dict(Counter(b for _, b in dates.values())),
            years=dict(sorted(Counter(dated.values()).items())),
            retrieved_share=rounded(sum(y >= cutoff for y in offered_years) / len(offered_years))
                            if offered_years else None,
            per_citation=rounded(sum(w for u, w in weights.items() if dated[u] >= cutoff)
                                 / sum(weights.values())) if sum(weights.values()) else None,
            old=[{"url": u, "year": y, "basis": dates[u][1]} for u, y in dated.items() if y < cutoff],
            undated_urls=[u for u, (y, _) in dates.items() if y is None])
        if not dated:
            return self.skip("no cited source names a year", **details)
        return self.result(rounded(sum(y >= cutoff for y in dated.values()) / len(dated)), **details)


class MaterialCoverage(Metric):
    """Share of the question's key points that the retrieved material covers,
    before any writing: the retrieval-side counterpart of comprehensiveness.

        value = (full + 0.5 partial key points) / key points

    Material = the chunks that reached the writer (`RunArchive.writer_chunk_ids`;
    failed deep steps' chunks never did). For each key point the evaluator,
    not the agent, picks the passages that match it best by BM25-weighted
    overlap, one per URL, `PASSAGES` per point; one judge call per run sees
    all points with their passages and grades each from any passage shown.
    The picks are a sample, so a point the material covers only in other
    words can be missed: a lower bound.

    Read beside the other two key-point metrics, per point (`details.per_point`):
    decomposition_coverage covered but material none -> searched, found
    nothing; material covered but comprehensiveness none -> found, not written.
    """

    name, category = "material_coverage", "retrieval.source"
    version = "1"
    uses_llm = True
    prompts = (MATERIAL_COVERAGE, KEY_POINTS)
    PASSAGES = 6
    PASSAGE_CHARS = 1200
    POINTS = {"full": 1.0, "partial": 0.5, "none": 0.0}

    def picks(self, archive: RunArchive, point: str, idf: dict) -> list[str]:
        scored = sorted(((weighted_overlap(point, set(tokenize(archive.chunks[c]["content"])), idf), i, c)
                         for i, c in enumerate(archive.writer_chunk_ids)), key=lambda x: (-x[0], x[1]))
        out, urls = [], set()
        for score, _, c in scored:
            url = normalize_url(archive.chunks[c].get("url") or c)
            if score <= 0 or url in urls:
                continue
            urls.add(url)
            out.append(c)
            if len(out) == self.PASSAGES:
                break
        return out

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self.skip("no judge configured")
        if not archive.writer_chunk_ids:
            return self.result(0.0, reason="no material reached the writer")
        points, provenance = await get_key_points(archive, ctx)
        if not points:
            return self.skip("no key points", key_points=provenance)
        idf = idf_table([archive.chunks[c]["content"] for c in archive.writer_chunk_ids])
        shown, blocks = {}, []
        for i, p in enumerate(points, 1):
            lines = [f"Key point {i}: {p}"]
            for j, c in enumerate(self.picks(archive, p, idf)):
                pid = f"{i}{ascii_lowercase[j]}"
                shown[pid] = c
                lines.append(f"[{pid}] {archive.chunks[c].get('url') or 'unknown source'}\n"
                             f"{archive.chunks[c]['content'][:self.PASSAGE_CHARS]}")
            if len(lines) == 1:
                lines.append("(no passage shares a word with this key point)")
            blocks.append("\n\n".join(lines))
        r = await ctx.judge.ask(MATERIAL_COVERAGE.id, MATERIAL_COVERAGE.version,
                                MATERIAL_COVERAGE.render(question=archive.query,
                                                         points="\n\n---\n\n".join(blocks)))
        got = {}
        for e in (r.parsed or {}).get("points", []) if isinstance(r.parsed, dict) else []:
            try:
                got[int(e["point"])] = e
            except (KeyError, TypeError, ValueError):
                continue
        if not got:
            res = self.skip("judge call failed", key_points=provenance, error=r.error)
            res.llm = self.llm_record(ctx, [r])
            return res
        per_point, total = [], 0.0
        for i, p in enumerate(points, 1):
            e = got.get(i, {})
            cov = str(e.get("coverage", "none")).lower()
            cov = cov if cov in self.POINTS else "none"
            total += self.POINTS[cov]
            cids = [shown[str(x)] for x in e.get("passages") or [] if str(x) in shown]
            per_point.append({"key_point": p, "coverage": cov, "answered": i in got,
                              "chunk_ids": cids,
                              "urls": list(dict.fromkeys(archive.chunks[c].get("url") for c in cids)),
                              "evidence": e.get("evidence", "")})
        res = self.result(rounded(total / len(points)), key_points=provenance, per_point=per_point,
                          uncovered=[x["key_point"] for x in per_point if x["coverage"] == "none"],
                          unanswered=sum(not x["answered"] for x in per_point),
                          passages_shown=len(shown), material_chunks=len(archive.writer_chunk_ids))
        res.llm = self.llm_record(ctx, [r])
        return res
