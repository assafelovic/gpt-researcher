"""
C. Efficiency metrics: whether what was retrieved was worth retrieving.
"""

from __future__ import annotations

from ...archive import RunArchive, normalize_url
from ...key_points import get_key_points
from ...prompts import KEY_POINTS, QUERY_RELEVANCE
from ...report_parser import body_paragraphs, cited_urls, paragraph_sentences, report_sentences
from ..base import Metric, MetricResult, ScoringContext, rounded
from ..lexical import idf_table, weighted_overlap

from gpt_researcher.context.lexical import tokenize


class CitationUtilization(Metric):
    """Share of retrieved source URLs that the report cites (rule-based, no LLM).

        value = cited URLs ∩ retrieved URLs / retrieved URLs

    Whether a specific chunk or claim was used is the generation metrics' job
    (ALCE-style citation recall / precision): matching a paragraph to the chunk
    behind it is the same machinery, and should live there once. Until then
    `details` carries a rule-based chunk diagnostic, not part of the value:

      chunk_level      chunks matched by a paragraph that cites their URL /
                       chunks. A chunk matches when the best sentence of such a
                       paragraph has >= `match` of its BM25-weighted terms in
                       the chunk. Chunks of uncited URLs never count as used:
                       many sources repeat the same facts, so content overlap
                       alone does not show a source was used.
      echoed_uncited   chunks of uncited URLs whose content the report still
                       echoes (best sentence anywhere >= `match`): material the
                       writer either took without citing or got elsewhere.
    """

    name, category = "citation_utilization", "retrieval.efficiency"
    version = "2"
    MATCH, MIN_TERMS = 0.5, 5

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        retrieved = archive.retrieved_urls
        if not retrieved:
            return self.skip("no retrieved sources")
        parsed = archive.report
        cited = {normalize_url(u) for u in cited_urls(parsed)}
        used_urls = [u for u in retrieved if normalize_url(u) in cited]
        threshold = ctx.option("utilization_match", self.MATCH)

        def usable(sentences):
            return [s for s in sentences if len(set(tokenize(s))) >= self.MIN_TERMS]

        by_url: dict[str, list[str]] = {}
        for p in body_paragraphs(parsed):
            sents = usable(paragraph_sentences(p))
            for c in p["citations"]:
                by_url.setdefault(normalize_url(c["url"]), []).extend(sents)
        all_sentences = usable(report_sentences(parsed))

        chunk_ids = archive.retrieved_chunk_ids
        idf = idf_table([archive.chunks[c]["content"] for c in chunk_ids])
        per_chunk, used, echoed = [], 0, 0
        for cid in chunk_ids:
            chunk = archive.chunks[cid]
            key = normalize_url(chunk["url"]) if chunk.get("url") else None
            terms = set(tokenize(chunk["content"]))
            is_cited = key in cited
            pool = by_url.get(key, []) if is_cited else all_sentences
            best = max((weighted_overlap(s, terms, idf) for s in pool), default=0.0)
            entry = {"chunk_id": cid, "url_cited": is_cited, "best_match": round(best, 3)}
            if is_cited:
                entry["used"] = best >= threshold
                used += entry["used"]
            else:
                entry["used"] = False
                entry["echoed_uncited"] = best >= threshold
                echoed += entry["echoed_uncited"]
            per_chunk.append(entry)

        return self.result(rounded(len(used_urls) / len(retrieved)),
                           retrieved_urls=len(retrieved), cited_retrieved_urls=len(used_urls),
                           uncited_urls=[u for u in retrieved if normalize_url(u) not in cited],
                           chunk_level=rounded(used / len(per_chunk)) if per_chunk else None,
                           chunks=len(per_chunk), chunks_used=used, chunks_echoed_uncited=echoed,
                           match_threshold=threshold, per_chunk=per_chunk)


class QueryRelevance(Metric):
    """Judge rubric on each search step packaged with its material.

    One call per search step that returned material (Q1 topic relevance, Q2
    key points hit, Q3 specificity, Q4 uniqueness, Q5 usability, then a 0-10
    total). v1 uses only the judge's total: value = mean(total / 10).

    Units: every executed sub-query except the run's core query, plus each
    researcher's initial (planning) search, which is often where the most-cited
    sources come from. Material: one representative chunk per source URL (the
    chunk that best matches the query by BM25 weighting), best URLs first,
    within a character budget, so the judge sees the breadth of what came back
    rather than the first few chunks of the first site. `details` records how
    many URLs and chunks each judge call saw.

    Steps that returned nothing are listed but not judged; plan_adherence
    already counts them.
    """

    name, category = "query_relevance", "retrieval.efficiency"
    version = "2"
    uses_llm = True
    prompts = (QUERY_RELEVANCE, KEY_POINTS)
    CHUNK_CHARS, MATERIAL_CHARS = 1500, 12000

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self.skip("no judge configured")
        core = archive.query.strip()
        units = [u for u in archive.retrieval_units
                 if u.kind == "initial_results"
                 or (u.kind == "sub_query" and u.query.strip() != core)]
        if not units:
            return self.skip("no executed sub-queries")
        points, provenance = await get_key_points(archive, ctx)
        if not points:
            return self.skip("no key points", key_points=provenance)
        judged = [u for u in units if u.chunk_ids]
        empty = [u.query for u in units if not u.chunk_ids]
        all_queries = list(dict.fromkeys(u.query for u in units if u.kind == "sub_query"))

        async def judge_one(u):
            material, shown = self._material(archive, u)
            label = (f"{u.query}\n(the initial search on this query, run while planning)"
                     if u.kind == "initial_results" else u.query)
            prompt = QUERY_RELEVANCE.render(
                question=archive.query,
                key_points="\n".join(f"{i}. {p}" for i, p in enumerate(points, 1)),
                other_queries="\n".join(f"- {q}" for q in all_queries if q != u.query) or "(none)",
                query=label, material=material)
            return u, shown, await ctx.judge.ask(QUERY_RELEVANCE.id, QUERY_RELEVANCE.version, prompt)

        results = await ctx.gather(judge_one(u) for u in judged)
        per_query, scores = [], []
        for u, shown, r in results:
            total = r.parsed.get("total") if isinstance(r.parsed, dict) else None
            try:
                norm = max(0.0, min(1.0, float(total) / 10))
            except (TypeError, ValueError):
                norm = None
            if norm is not None:
                scores.append(norm)
            per_query.append({"span_id": u.span_id, "kind": u.kind, "query": u.query,
                              "chunks": len(u.chunk_ids), **shown,
                              "score": rounded(norm), "rubric": r.parsed, "error": r.error})
        res = self.result(rounded(sum(scores) / len(scores)) if scores else None,
                          key_points=provenance, judged=len(scores),
                          no_material=empty, per_query=per_query)
        if judged and not scores:
            res.skipped = "every judge call failed"
        elif not judged:
            res.skipped = "no sub-query returned material"
        res.llm = self.llm_record(ctx, [r for _, _, r in results])
        return res

    def _material(self, archive: RunArchive, unit) -> tuple[str, dict]:
        """One best-matching chunk per URL, best URLs first, within the budget."""
        chunks = [(cid, archive.chunks[cid]) for cid in unit.chunk_ids if cid in archive.chunks]
        idf = idf_table([c["content"] for _, c in chunks])
        best: dict[str, tuple[float, dict]] = {}
        for _, c in chunks:
            key = normalize_url(c["url"]) if c.get("url") else f"unattributed:{id(c)}"
            score = weighted_overlap(unit.query, set(tokenize(c["content"])), idf)
            if key not in best or score > best[key][0]:
                best[key] = (score, c)
        parts, used = [], 0
        for _, c in sorted(best.values(), key=lambda x: -x[0]):
            block = f"[{c.get('url') or 'unknown source'}]\n{c['content'][:self.CHUNK_CHARS]}"
            if used + len(block) > self.MATERIAL_CHARS and parts:
                break
            parts.append(block)
            used += len(block)
        return "\n\n".join(parts), {"urls_total": len(best), "urls_shown": len(parts)}


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
