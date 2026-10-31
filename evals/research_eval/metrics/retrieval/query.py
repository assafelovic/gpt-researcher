"""
A. Query metrics: what the agent decided to search for.
"""

from __future__ import annotations

from itertools import combinations

from ...archive import RunArchive
from ...judge import cosine
from ...key_points import get_key_points
from ...prompts import DECOMPOSITION_COVERAGE, KEY_POINTS, TREE_QUALITY
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
    question). One judge call then maps every key point to the sub-queries
    that target it, quoting the sub-query as evidence. Covered = at least one
    sub-query. Whole-query embedding similarity proved unreliable for this
    (a query naming four regulations is close to none of them, a query about
    the EU looked close to a UK key point), so embeddings are only a fallback
    when no judge is configured, flagged in `details.method`.
    """

    name, category = "decomposition_coverage", "retrieval.query"
    version = "2"
    uses_llm = True
    prompts = (KEY_POINTS, DECOMPOSITION_COVERAGE)
    EMBEDDING_THRESHOLD = 0.5

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None and ctx.embedder is None:
            return self.skip("no judge or embedder configured")
        points, provenance = await get_key_points(archive, ctx)
        if not points:
            return self.skip("no key points", key_points=provenance)
        queries = all_subqueries(archive)
        if not queries:
            return self.result(0.0, key_points=provenance, per_point=[], reason="no sub-queries")
        if ctx.judge is None:
            return await self._by_embedding(points, queries, provenance, ctx)

        prompt = DECOMPOSITION_COVERAGE.render(
            question=archive.query,
            key_points="\n".join(f"{i}. {p}" for i, p in enumerate(points, 1)),
            subqueries="\n".join(f"{i}. {q}" for i, q in enumerate(queries, 1)))
        r = await ctx.judge.ask(DECOMPOSITION_COVERAGE.id, DECOMPOSITION_COVERAGE.version, prompt)
        entries = r.parsed.get("points") if isinstance(r.parsed, dict) else None
        by_point = {}
        for e in entries if isinstance(entries, list) else []:
            try:
                by_point[int(e["point"])] = e
            except (KeyError, TypeError, ValueError):
                continue
        if not by_point:
            res = self.skip("judge call failed", key_points=provenance, error=r.error, raw=r.raw[:500])
            res.llm = self.llm_record(ctx, [r])
            return res
        per_point = []
        for i, p in enumerate(points, 1):
            e = by_point.get(i, {})
            nums = [n for n in e.get("subqueries") or [] if isinstance(n, int) and 1 <= n <= len(queries)]
            per_point.append({"key_point": p, "covered": bool(nums),
                              "subqueries": [queries[n - 1] for n in nums],
                              "evidence": e.get("evidence"), "answered": i in by_point})
        covered = sum(x["covered"] for x in per_point)
        res = self.result(rounded(covered / len(points)), method="judge", key_points=provenance,
                          n_subqueries=len(queries), per_point=per_point)
        res.llm = self.llm_record(ctx, [r])
        return res

    async def _by_embedding(self, points, queries, provenance, ctx) -> MetricResult:
        threshold = ctx.option("coverage_threshold", self.EMBEDDING_THRESHOLD)
        vecs = await ctx.embedder.embed(points + queries)
        pv, qv = vecs[:len(points)], vecs[len(points):]
        per_point = []
        for p, v in zip(points, pv):
            sims = [cosine(v, w) for w in qv]
            best = max(range(len(sims)), key=sims.__getitem__)
            per_point.append({"key_point": p, "best_similarity": round(sims[best], 4),
                              "subqueries": [queries[best]] if sims[best] >= threshold else [],
                              "covered": sims[best] >= threshold})
        covered = sum(x["covered"] for x in per_point)
        return self.result(rounded(covered / len(points)), method="embedding_fallback",
                           threshold=threshold, embedding_model=ctx.embedder.model,
                           key_points=provenance, n_subqueries=len(queries), per_point=per_point)


class SubqueryRedundancy(Metric):
    """Share of search steps that ask what another step already asks (lower is better).

    With a judge: read from query_relevance's Q4 ("compared with the other
    sub-queries, does this one go after something they do not?"), which is
    already paid for. Each step is compared with the steps at the same layer
    of the query tree only (`RunArchive.query_layer`), across branches: a
    parent and its own children overlap by design. Only a step that asks for
    the same information as another in other words is not unique; another
    perspective, source or separate subtopic of the same object is. value =
    steps judged not unique / steps with a Q4 answer.

    Without a judge (`details.method` = "lexical"): sibling pairs whose
    symmetric BM25-weighted term overlap reaches the threshold, IDF over the
    sibling group. Kept as a fallback only: with three or four siblings the
    group IDF gives shared words so little weight that near-duplicates score
    well under the threshold, and branches are never compared.
    """

    name, category = "subquery_redundancy", "retrieval.query"
    version = "4"           # 4: only a reworded request for the same facts is a duplicate
    higher_is_better = False
    DEFAULT_THRESHOLD = 0.6

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self._lexical(archive, ctx)
        from .efficiency import QueryRelevance
        qr = await QueryRelevance().score(archive, ctx)
        if qr.value is None:
            res = self.skip(f"query_relevance: {qr.skipped}")
            res.llm = {**(qr.llm or {}), "shared": "query_relevance"}
            return res
        steps = []
        for q in qr.details["per_query"]:
            q4 = (q.get("rubric") or {}).get("q4") if isinstance(q.get("rubric"), dict) else None
            unique = q4.get("unique") if isinstance(q4, dict) else None
            if isinstance(unique, str):
                unique = {"true": True, "false": False}.get(unique.strip().lower())
            if isinstance(unique, bool):
                steps.append({"span_id": q["span_id"], "kind": q["kind"], "query": q["query"],
                              "unique": unique, "evidence": q4.get("evidence", "")})
        if not steps:
            return self.skip("query_relevance returned no uniqueness answers")
        dupes = [x for x in steps if not x["unique"]]
        res = self.result(rounded(len(dupes) / len(steps)), method="judge_q4",
                          steps=len(steps), not_unique=dupes)
        res.llm = {**(qr.llm or {}), "shared": "query_relevance"}
        return res

    def _lexical(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
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
        return self.result(rounded(len(dupes) / pairs_total), method="lexical", threshold=threshold,
                           pairs=pairs_total, duplicate_pairs=dupes, groups=groups)


class DecompositionTreeQuality(Metric):
    """Judge rubric per parent node: coverage, specificity, searchability,
    relevance to the parent, and relevance to the original question (Q5, which
    catches a deep tree drifting away from the question one level at a time).

    One call per decomposition (parent + all its children). The judge also sees
    the whole path from the original question down to the parent
    (`RunArchive.query_path`), so Q5 can follow drift across levels. Each call
    returns a 0-10 total; the value is the mean of total/10 over parents.
    """

    name, category = "decomposition_tree_quality", "retrieval.query"
    version = "3"           # 3: the judge sees the root-to-parent path
    MAX_TOTAL = 10
    uses_llm = True
    prompts = (TREE_QUALITY,)

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self.skip("no judge configured")
        decs = [d for d in archive.decompositions if d.child_queries]
        if not decs:
            return self.skip("no decompositions")

        async def judge_one(d):
            path = archive.query_path(d.span_id)
            if path[-1] != d.parent_query.strip():
                path.append(d.parent_query.strip())
            prompt = TREE_QUALITY.render(
                question=archive.query.strip(),
                path="\n".join(f"{i}. {self._short(q)}" for i, q in enumerate(path)),
                parent=d.parent_query.strip(),
                children="\n".join(f"- {c}" for c in d.child_queries))
            return d, await ctx.judge.ask(TREE_QUALITY.id, TREE_QUALITY.version, prompt)

        results = await ctx.gather(judge_one(d) for d in decs)
        per_parent, scores = [], []
        for d, r in results:
            total = _number((r.parsed or {}).get("total")) if isinstance(r.parsed, dict) else None
            norm = None if total is None else max(0.0, min(1.0, total / self.MAX_TOTAL))
            if norm is not None:
                scores.append(norm)
            per_parent.append({"span_id": d.span_id, "kind": d.kind, "parent": d.parent_query,
                               "depth": len(archive.query_path(d.span_id)) - 1,
                               "n_children": len(d.child_queries), "score": rounded(norm),
                               "rubric": r.parsed, "error": r.error})
        res = self.result(rounded(sum(scores) / len(scores)) if scores else None,
                          per_parent=per_parent, scored_parents=len(scores))
        if not scores:
            res.skipped = "every judge call failed"
        res.llm = self.llm_record(ctx, [r for _, r in results])
        return res

    PATH_CHARS = 400

    @classmethod
    def _short(cls, q: str) -> str:
        q = " ".join(q.split())
        return q if len(q) <= cls.PATH_CHARS else q[:cls.PATH_CHARS] + " ..."


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
