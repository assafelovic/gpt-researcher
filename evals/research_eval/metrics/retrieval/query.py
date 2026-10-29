"""
A. Query metrics: what the agent decided to search for.
"""

from __future__ import annotations

from itertools import combinations

from ...archive import RunArchive
from ...judge import cosine
from ...key_points import get_key_points
from ...prompts import KEY_POINTS, TREE_QUALITY
from ..base import Metric, MetricResult, ScoringContext, rounded
from ..lexical import idf_table, symmetric_overlap


def all_subqueries(archive: RunArchive) -> list[str]:
    """Every child query the run produced or searched, minus the core query."""
    seen, out = {archive.query.strip()}, []
    for q in [c for d in archive.decompositions for c in d.child_queries] + archive.issued_subqueries:
        q = (q or "").strip()
        if q and q not in seen:
            seen.add(q)
            out.append(q)
    return out


class DecompositionCoverage(Metric):
    """Share of the question's key points that some sub-query is aimed at.

    Key points come from get_key_points (frozen / cached / one judge call per
    question). Sub-queries and key points are embedded; a key point is covered
    when its best cosine similarity to any sub-query reaches the threshold.
    The threshold is uncalibrated in v1: per-point best similarities are kept
    in `details` so it can be tuned against human labels.
    """

    name, category = "decomposition_coverage", "retrieval.query"
    uses_llm = uses_embeddings = True
    prompts = (KEY_POINTS,)
    DEFAULT_THRESHOLD = 0.5

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.embedder is None:
            return self.skip("no embedder configured")
        points, provenance = await get_key_points(archive, ctx)
        if not points:
            return self.skip("no key points", key_points=provenance)
        queries = all_subqueries(archive)
        if not queries:
            return self.result(0.0, key_points=provenance, covered=[], reason="no sub-queries")
        threshold = ctx.option("coverage_threshold", self.DEFAULT_THRESHOLD)
        vecs = await ctx.embedder.embed(points + queries)
        pv, qv = vecs[:len(points)], vecs[len(points):]
        per_point = []
        for p, v in zip(points, pv):
            sims = [cosine(v, w) for w in qv]
            best = max(range(len(sims)), key=sims.__getitem__)
            per_point.append({"key_point": p, "best_similarity": round(sims[best], 4),
                              "best_subquery": queries[best], "covered": sims[best] >= threshold})
        covered = sum(x["covered"] for x in per_point)
        return self.result(rounded(covered / len(points)), threshold=threshold,
                           embedding_model=ctx.embedder.model, key_points=provenance,
                           n_subqueries=len(queries), per_point=per_point)


class SubqueryRedundancy(Metric):
    """Share of sibling sub-query pairs that ask the same thing (lower is better).

    Siblings are the children of one decomposition. Two siblings are a
    duplicate when their symmetric BM25-weighted term overlap reaches the
    threshold; IDF is computed over the sibling group, so the core-topic words
    every sibling shares carry little weight.
    """

    name, category = "subquery_redundancy", "retrieval.query"
    higher_is_better = False
    DEFAULT_THRESHOLD = 0.6

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        threshold = ctx.option("redundancy_threshold", self.DEFAULT_THRESHOLD)
        pairs_total, dupes, groups = 0, [], []
        for d in archive.decompositions:
            kids = list(dict.fromkeys(d.child_queries))
            if len(kids) < 2:
                continue
            idf = idf_table(kids)
            n_pairs = 0
            for a, b in combinations(kids, 2):
                n_pairs += 1
                sim = symmetric_overlap(a, b, idf)
                if sim >= threshold:
                    dupes.append({"span_id": d.span_id, "a": a, "b": b, "similarity": round(sim, 3)})
            pairs_total += n_pairs
            groups.append({"span_id": d.span_id, "kind": d.kind, "pairs": n_pairs})
        if not pairs_total:
            return self.skip("no decomposition with two or more children")
        return self.result(rounded(len(dupes) / pairs_total), threshold=threshold,
                           pairs=pairs_total, duplicate_pairs=dupes, groups=groups)


class DecompositionTreeQuality(Metric):
    """Judge rubric per parent node: coverage, specificity, searchability, relevance.

    One call per decomposition (parent + all its children). Each call returns a
    0-8 total; the value is the mean of total/8 over parents.
    """

    name, category = "decomposition_tree_quality", "retrieval.query"
    uses_llm = True
    prompts = (TREE_QUALITY,)

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self.skip("no judge configured")
        decs = [d for d in archive.decompositions if d.child_queries]
        if not decs:
            return self.skip("no decompositions")

        async def judge_one(d):
            prompt = TREE_QUALITY.render(
                parent=d.parent_query.strip(),
                children="\n".join(f"- {c}" for c in d.child_queries))
            return d, await ctx.judge.ask(TREE_QUALITY.id, TREE_QUALITY.version, prompt)

        results = await ctx.gather(judge_one(d) for d in decs)
        per_parent, scores = [], []
        for d, r in results:
            total = _number((r.parsed or {}).get("total")) if isinstance(r.parsed, dict) else None
            norm = None if total is None else max(0.0, min(1.0, total / 8))
            if norm is not None:
                scores.append(norm)
            per_parent.append({"span_id": d.span_id, "kind": d.kind, "parent": d.parent_query,
                               "n_children": len(d.child_queries), "score": rounded(norm),
                               "rubric": r.parsed, "error": r.error})
        res = self.result(rounded(sum(scores) / len(scores)) if scores else None,
                          per_parent=per_parent, scored_parents=len(scores))
        if not scores:
            res.skipped = "every judge call failed"
        res.llm = self.llm_record(ctx, [r for _, r in results])
        return res


class PlanAdherence(Metric):
    """Share of planned sub-queries that came back with material.

    A planned child counts when the step that executed it ended with at least
    one chunk: for a "plan" node, its sub_query span; for a deep-research
    level, the nested researcher (any chunk in its subtree); for detailed
    subtopics, the subtopic researcher. A child that was never executed counts
    as not delivered. Deep-research clarifying questions are folded into a
    combined query rather than searched one by one, so they are not counted.
    """

    name, category = "plan_adherence", "retrieval.query"

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        planned = delivered = 0
        failures, per_kind = [], {}
        for d in archive.decompositions:
            if d.kind == "deep_plan":
                continue
            for q in d.child_queries:
                ok = self._delivered(archive, d, q)
                planned += 1
                delivered += ok
                k = per_kind.setdefault(d.kind, {"planned": 0, "delivered": 0})
                k["planned"] += 1
                k["delivered"] += ok
                if not ok:
                    failures.append({"span_id": d.span_id, "kind": d.kind, "query": q})
        if not planned:
            return self.skip("no plan recorded")
        return self.result(rounded(delivered / planned), planned=planned, delivered=delivered,
                           per_kind=per_kind, not_delivered=failures)

    @staticmethod
    def _delivered(archive: RunArchive, d, query: str) -> bool:
        if d.kind == "plan":
            spans = [s for s in archive.children.get(d.span_id, [])
                     if s["name"] == "sub_query" and s["attributes"].get("query") == query]
            return any(s["attributes"].get("chunk_ids") for s in spans)
        if d.kind == "deep_level":
            spans = [s for s in archive.children.get(d.span_id, [])
                     if s["name"] == "research" and s["attributes"].get("query") == query]
        else:  # subtopics
            spans = [s for s in archive.spans
                     if s["name"] == "research" and s["attributes"].get("query") == query
                     and s["attributes"].get("parent_query")]
        return any(archive.subtree_chunk_ids(s["span_id"]) for s in spans)


def _number(x) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None
