"""
C. Efficiency metrics: whether what was retrieved was worth retrieving.
"""

from __future__ import annotations

from ...archive import RunArchive, normalize_url
from ...key_points import get_key_points
from ...prompts import CHUNK_USED, KEY_POINTS, QUERY_RELEVANCE
from ...report_parser import cited_urls, report_sentences
from ..base import Metric, MetricResult, ScoringContext, rounded
from ..lexical import idf_table, weighted_overlap

from gpt_researcher.context.lexical import tokenize


class CitationUtilization(Metric):
    """How much of the retrieved material ended up in the report.

    Two levels, combined as their mean:

      url_level    cited URLs ∩ retrieved URLs / retrieved URLs
      chunk_level  used chunks / decided chunks. For each chunk, the report
                   sentence it best matches is found with BM25 term weighting
                   (share of the sentence's weight present in the chunk).
                   >= high: used; < low: not used; in between: one judge call
                   per chunk, at most `max_borderline` of them. Borderline
                   chunks over the cap, or whose call failed, stay undecided
                   and are left out of the denominator.
    """

    name, category = "citation_utilization", "retrieval.efficiency"
    uses_llm = True
    prompts = (CHUNK_USED,)
    HIGH, LOW, MAX_BORDERLINE, MIN_TERMS = 0.7, 0.4, 20, 5

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        retrieved = archive.retrieved_urls
        if not archive.retrieved_chunk_ids:
            return self.skip("no retrieved chunks")
        parsed = archive.report
        cited = {normalize_url(u) for u in cited_urls(parsed)}
        used_urls = [u for u in retrieved if normalize_url(u) in cited]
        url_level = len(used_urls) / len(retrieved) if retrieved else None

        high = ctx.option("utilization_high", self.HIGH)
        low = ctx.option("utilization_low", self.LOW)
        cap = ctx.option("utilization_max_borderline", self.MAX_BORDERLINE)

        sentences = [s for s in report_sentences(parsed) if len(set(tokenize(s))) >= self.MIN_TERMS]
        chunk_ids = archive.retrieved_chunk_ids
        contents = [archive.chunks[c]["content"] for c in chunk_ids]
        idf = idf_table(contents)
        per_chunk, borderline = [], []
        for cid, content in zip(chunk_ids, contents):
            terms = set(tokenize(content))
            sims = sorted(((weighted_overlap(s, terms, idf), s) for s in sentences), reverse=True)
            best = sims[0][0] if sims else 0.0
            entry = {"chunk_id": cid, "best_match": round(best, 3),
                     "sentence": sims[0][1] if sims else None}
            if best >= high:
                entry["used"], entry["basis"] = True, "lexical"
            elif best < low:
                entry["used"], entry["basis"] = False, "lexical"
            else:
                entry["used"], entry["basis"] = None, "borderline"
                borderline.append((entry, content, [s for _, s in sims[:3]]))
            per_chunk.append(entry)

        borderline.sort(key=lambda x: -x[0]["best_match"])
        to_judge, over_cap = borderline[:cap], borderline[cap:]
        responses = []
        if to_judge and ctx.judge is not None:
            async def judge_one(item):
                entry, content, top = item
                prompt = CHUNK_USED.render(chunk=content[:4000],
                                           sentences="\n".join(f"- {s}" for s in top))
                return entry, await ctx.judge.ask(CHUNK_USED.id, CHUNK_USED.version, prompt)

            for entry, r in await ctx.gather(judge_one(i) for i in to_judge):
                responses.append(r)
                used = r.parsed.get("used") if isinstance(r.parsed, dict) else None
                if isinstance(used, bool):
                    entry["used"], entry["basis"] = used, "judge"
        for entry, _, _ in over_cap:
            entry["basis"] = "borderline_over_cap"

        decided = [e for e in per_chunk if e["used"] is not None]
        chunk_level = sum(e["used"] for e in decided) / len(decided) if decided else None
        parts = [x for x in (url_level, chunk_level) if x is not None]
        res = self.result(rounded(sum(parts) / len(parts)) if parts else None,
                          url_level=rounded(url_level), chunk_level=rounded(chunk_level),
                          retrieved_urls=len(retrieved), cited_retrieved_urls=len(used_urls),
                          chunks=len(per_chunk), chunks_decided=len(decided),
                          chunks_undecided=len(per_chunk) - len(decided),
                          thresholds={"high": high, "low": low, "max_borderline": cap},
                          per_chunk=per_chunk)
        res.llm = self.llm_record(ctx, responses)
        return res


class QueryRelevance(Metric):
    """Judge rubric on each sub-query packaged with its material.

    One call per executed sub-query that returned material (Q1 topic relevance,
    Q2 key points hit, Q3 specificity, Q4 uniqueness, Q5 usability, then a
    0-10 total). v1 uses only the judge's total: value = mean(total / 10).
    Sub-queries that returned nothing are listed but not judged; plan_adherence
    already counts them. The run's core query is not a sub-query and is not
    judged; nested researchers' root queries (deep SERP queries, subtopics) are.
    """

    name, category = "query_relevance", "retrieval.efficiency"
    uses_llm = True
    prompts = (QUERY_RELEVANCE, KEY_POINTS)
    CHUNK_CHARS, MATERIAL_CHARS = 1500, 6000

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self.skip("no judge configured")
        core = archive.query.strip()
        units = [u for u in archive.retrieval_units
                 if u.kind == "sub_query" and u.query.strip() != core]
        if not units:
            return self.skip("no executed sub-queries")
        points, provenance = await get_key_points(archive, ctx)
        if not points:
            return self.skip("no key points", key_points=provenance)
        judged = [u for u in units if u.chunk_ids]
        empty = [u.query for u in units if not u.chunk_ids]
        all_queries = list(dict.fromkeys(u.query for u in units))

        async def judge_one(u):
            prompt = QUERY_RELEVANCE.render(
                question=archive.query,
                key_points="\n".join(f"{i}. {p}" for i, p in enumerate(points, 1)),
                other_queries="\n".join(f"- {q}" for q in all_queries if q != u.query) or "(none)",
                query=u.query,
                material=self._material(archive, u.chunk_ids))
            return u, await ctx.judge.ask(QUERY_RELEVANCE.id, QUERY_RELEVANCE.version, prompt)

        results = await ctx.gather(judge_one(u) for u in judged)
        per_query, scores = [], []
        for u, r in results:
            total = r.parsed.get("total") if isinstance(r.parsed, dict) else None
            try:
                norm = max(0.0, min(1.0, float(total) / 10))
            except (TypeError, ValueError):
                norm = None
            if norm is not None:
                scores.append(norm)
            per_query.append({"span_id": u.span_id, "query": u.query, "chunks": len(u.chunk_ids),
                              "score": rounded(norm), "rubric": r.parsed, "error": r.error})
        res = self.result(rounded(sum(scores) / len(scores)) if scores else None,
                          key_points=provenance, judged=len(scores),
                          no_material=empty, per_query=per_query)
        if judged and not scores:
            res.skipped = "every judge call failed"
        elif not judged:
            res.skipped = "no sub-query returned material"
        res.llm = self.llm_record(ctx, [r for _, r in results])
        return res

    def _material(self, archive: RunArchive, chunk_ids: list[str]) -> str:
        parts, used = [], 0
        for cid in chunk_ids:
            c = archive.chunks.get(cid)
            if not c:
                continue
            block = f"[{c.get('url') or 'unknown source'}]\n{c['content'][:self.CHUNK_CHARS]}"
            if used + len(block) > self.MATERIAL_CHARS and parts:
                break
            parts.append(block)
            used += len(block)
        return "\n\n".join(parts)


class RetrievalOverlap(Metric):
    """Share of search results already returned to an earlier query (lower is better).

    Measured at URL de-duplication (`_get_new_urls`): the only point where the
    overlap is still visible, since everything downstream sees disjoint sets.
    Pre-fetched results from retrievers that return content bypass that step
    and are not counted.
    """

    name, category = "retrieval_overlap", "retrieval.efficiency"
    higher_is_better = False

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        proposed = sum(len(u.proposed_urls) for u in archive.retrieval_units)
        accepted = sum(len(u.new_urls) for u in archive.retrieval_units)
        if not proposed:
            return self.skip("no search results recorded")
        per_unit = [{"span_id": u.span_id, "query": u.query, "proposed": len(u.proposed_urls),
                     "new": len(u.new_urls)} for u in archive.retrieval_units if u.proposed_urls]
        return self.result(rounded((proposed - accepted) / proposed), proposed=proposed,
                           new=accepted, duplicate=proposed - accepted, per_unit=per_unit)
