"""
A. Query metrics: what the agent decided to search for.
"""

from __future__ import annotations

from itertools import combinations

from ...archive import RunArchive
from ...judge import cosine
from ...key_points import get_key_points
from ...prompts import DECOMPOSITION_COVERAGE, KEY_POINTS, SUBQUERY_REDUNDANCY, TREE_QUALITY
from ..base import Metric, MetricResult, ScoringContext, rounded
from ..lexical import idf_table, symmetric_overlap


def all_subqueries(archive: RunArchive) -> list[str]:
    """Every child query the run produced or searched, minus the core query.

    Deep research's clarifying questions (deep_plan) are left out: they are
    folded into one combined query, never searched one by one.
    """
    seen, out = {archive.query.strip()}, []
    planned = [c for d in archive.decompositions if d.kind != "deep_plan" for c in d.child_queries]
    for q in planned + archive.issued_subqueries:
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

    name, category = "decomposition_coverage", "retrieval.query_quality"
    version = "3"           # 3: deep clarifying questions are not sub-queries
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
    """Share of query-tree nodes that repeat another node of the tree (lower is better).

    Nodes are `RunArchive.query_nodes`: every searched query below the run's
    question, both branches (a researcher's own question, split further) and
    leaves (planned sub-queries), whether or not their search brought back
    new material. Any two nodes are compared, at any layer and in any branch,
    except a node and the nodes it was split from (its ancestors,
    `RunArchive.query_node_ancestors`): those overlap by design.

    With a judge: the judge sees every node in search order, each with the
    numbers of its ancestors, and marks each node that asks for the same
    information as an earlier node in other words (the same facts would
    answer both). Another perspective, source, period, place, a separate
    subtopic, or a narrower part of a broader query is not a repeat. A mark
    that points at an ancestor or a descendant is dropped
    (`details.dropped_marks`). Borderline marks flip from one call to the
    next, so the same prompt is asked VOTES times (cache keys apart) and a
    node is a repeat when a majority of the replies mark it; its original is
    the node most of those marks name. `details.unstable` lists the nodes
    some but not all replies marked. Repeats chain into groups; in each
    group the node searched first is the original and the rest are
    duplicates.

        value = duplicate nodes / all nodes

    `details.per_layer` and `details.per_kind` (branch / leaf) give the share
    by the duplicate's layer and kind; `details.same_layer` and
    `details.same_parent` count the duplicates whose original sits on the
    same layer / has the same parent (the per-layer comparison of v6 would
    only see the first). A node no reply answers counts as not a duplicate
    and is listed in `details.unanswered`.

    Without a judge (`details.method` = "lexical"): sibling pairs whose
    symmetric BM25-weighted term overlap reaches the threshold, IDF over the
    sibling group. Kept as a fallback only: with three or four siblings the
    group IDF gives shared words so little weight that near-duplicates score
    well under the threshold, and branches are never compared.
    """

    name, category = "subquery_redundancy", "retrieval.query_quality"
    version = "9"           # 4: only a reworded request for the same facts; 5: sub-queries only;
                            # 6: own call per layer over every node; 7: whole tree but ancestors, one call;
                            # 8: overlaps beside repeats (too broad, dropped); 9: majority of VOTES calls
    higher_is_better = False
    uses_llm = True         # the lexical fallback only runs when no judge is configured at all
    prompts = (SUBQUERY_REDUNDANCY,)
    DEFAULT_THRESHOLD = 0.6
    VOTES = 3

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self._lexical(archive, ctx)
        nodes = archive.query_nodes
        if not nodes:
            return self.skip("no searched query below the run's question")
        index = {n.span_id: i for i, n in enumerate(nodes, 1)}
        above = {i: {index[a] for a in archive.query_node_ancestors[n.span_id]} for i, n in enumerate(nodes, 1)}
        related = lambda i, j: i in above[j] or j in above[i]
        if len(nodes) == 1:
            return self.result(0.0, method="judge_tree", nodes=1, duplicates=0, reason="one node")

        lines = []
        for i, n in enumerate(nodes, 1):
            path = [index[a] for a in reversed(archive.query_node_ancestors[n.span_id])]
            tag = f" [{' > '.join(map(str, path))}]" if path else ""
            lines.append(f"{i}.{tag} {' '.join(n.query.split())}")
        prompt = SUBQUERY_REDUNDANCY.render(question=archive.query.strip(), queries="\n".join(lines))
        votes = max(1, int(ctx.option("redundancy_votes", self.VOTES)))
        # The first call keeps the plain cache key, so a single-call verdict is reused.
        replies = await ctx.gather(
            ctx.judge.ask(SUBQUERY_REDUNDANCY.id, SUBQUERY_REDUNDANCY.version, prompt, **({"vote": k} if k else {}))
            for k in range(votes))
        ballots = [r.parsed.get("queries") for r in replies
                   if isinstance(r.parsed, dict) and isinstance(r.parsed.get("queries"), list)]
        if not ballots:
            res = self.skip("judge call failed", errors=[r.error for r in replies],
                            raw=(replies[0].raw or "")[:300])
            res.llm = self.llm_record(ctx, replies)
            return res

        marks: dict[int, list[tuple[int, str]]] = {}
        answered, dropped = set(), {}
        for entries in ballots:
            for e in entries:
                try:
                    i = int(e["query"])
                except (KeyError, TypeError, ValueError):
                    continue
                if not 1 <= i <= len(nodes):
                    continue
                answered.add(i)
                j = None if isinstance(e.get("repeats"), bool) else _number(e.get("repeats"))
                if j is None or j != int(j) or not 1 <= j <= len(nodes) or j == i:
                    continue
                j = int(j)
                if related(i, j):
                    dropped[(i, j)] = {"query": nodes[i - 1].query, "marked": nodes[j - 1].query}
                    continue
                marks.setdefault(i, []).append((j, str(e.get("evidence") or "")))
        need = len(ballots) // 2 + 1
        links, unstable = {}, []
        for i, ms in sorted(marks.items()):
            targets = [j for j, _ in ms]
            j = min(set(targets), key=lambda t: (-targets.count(t), t))
            if len(ms) < len(ballots):
                unstable.append({"query": nodes[i - 1].query, "repeats": nodes[j - 1].query,
                                 "marks": len(ms), "replies": len(ballots), "counted": len(ms) >= need})
            if len(ms) >= need:
                links[i] = (j, next(ev for t, ev in ms if t == j))
        # Groups of repeats; the node searched first is each group's original.
        group = list(range(len(nodes) + 1))
        find = lambda x: x if group[x] == x else find(group[x])
        for i, (j, _) in links.items():
            a, b = sorted((find(i), find(j)))
            group[b] = a
        members: dict[int, list[int]] = {}
        for i in range(1, len(nodes) + 1):
            members.setdefault(find(i), []).append(i)
        duplicates = []
        for i, n in enumerate(nodes, 1):
            if find(i) == i:
                continue
            j, evidence = links.get(i, (None, ""))
            if j is None:                       # in a group only through another node's mark
                j = next((k for k in members[find(i)] if k != i and not related(i, k)), find(i))
            o = nodes[j - 1]
            duplicates.append({"query": n.query, "layer": n.layer, "kind": n.kind, "repeats": o.query,
                               "repeats_layer": o.layer, "same_layer": o.layer == n.layer,
                               "same_parent": o.parent == n.parent, "evidence": evidence,
                               "span_id": n.span_id})
        dup_ids = {d["span_id"] for d in duplicates}

        def share(xs):
            k = sum(x.span_id in dup_ids for x in xs)
            return {"nodes": len(xs), "duplicates": k, "share": rounded(k / len(xs)) if xs else None}

        by = lambda key: {k: share([n for n in nodes if getattr(n, key) == k])
                          for k in sorted({getattr(n, key) for n in nodes})}
        res = self.result(
            rounded(len(dup_ids) / len(nodes)), method="judge_tree", nodes=len(nodes),
            duplicates=len(dup_ids), same_layer=sum(d["same_layer"] for d in duplicates),
            same_parent=sum(d["same_parent"] for d in duplicates),
            per_layer=by("layer"), per_kind=by("kind"), votes=votes, replies=len(ballots),
            not_unique=duplicates, unstable=unstable,
            unanswered=[nodes[i - 1].query for i in range(1, len(nodes) + 1) if i not in answered],
            dropped_marks=list(dropped.values()))
        res.llm = self.llm_record(ctx, replies)
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

    name, category = "decomposition_tree_quality", "retrieval.query_quality"
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
    """Share of planned sub-queries whose step was carried out: it came back
    with material, and that material went on to the rest of the pipeline.

        value = completed planned sub-queries / planned sub-queries

    A planned child counts when the step that executed it ended with at least
    one chunk: for a "plan" node, its sub_query span; for a deep-research
    level, the nested researcher (any chunk in its subtree); for detailed
    subtopics, the subtopic researcher. A deep-research step must also not
    have failed afterwards: when processing its results raises, the step is
    dropped (process_query returns None) and none of its material reaches the
    next level or the writer (`RunArchive.failed_deep_steps`), so it counts as
    not completed. A child that was never executed counts as not completed.
    Deep-research clarifying questions are folded into a combined query
    rather than searched one by one, so they are not counted.

    `details.retrieval_delivery` = planned sub-queries that came back with
    material / planned, the v2 value; `failed_after_retrieval` lists the
    steps that make the difference.
    """

    name, category = "plan_adherence", "retrieval.retrieval_quality"
    version = "3"           # 2: deep steps with material but no learnings in details; 3: failed deep steps count as not completed

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        lost = {s["span_id"] for s in archive.failed_deep_steps}
        planned = delivered = completed = 0
        failures, failed_after, per_kind = [], [], {}
        for d in archive.decompositions:
            if d.kind == "deep_plan":
                continue
            for q in d.child_queries:
                spans = self._delivering(archive, d, q)
                ok = bool(spans)
                done = any(s["span_id"] not in lost for s in spans)
                planned += 1
                delivered += ok
                completed += done
                k = per_kind.setdefault(d.kind, {"planned": 0, "delivered": 0, "completed": 0})
                k["planned"] += 1
                k["delivered"] += ok
                k["completed"] += done
                if not ok:
                    failures.append({"span_id": d.span_id, "kind": d.kind, "query": q})
                elif not done:
                    failed_after.append({"span_id": d.span_id, "kind": d.kind, "query": q,
                                         "error": next((s["attributes"].get("process_error")
                                                        for s in spans if s["attributes"].get("process_error")),
                                                       None)})
        if not planned:
            return self.skip("no plan recorded")
        # Deep research: a step can also finish with material but no learnings
        # (e.g. the LLM answered empty). Its material still reaches the writer,
        # so it counts as completed; it is listed here.
        steps = [s for s in archive.spans if s["name"] == "research"
                 and (archive.span_by_id.get(s["parent_id"]) or {}).get("name") == "deep_level"]
        extra = {}
        if steps:
            with_material = [s for s in steps if archive.subtree_chunk_ids(s["span_id"])]
            no_learnings = [s["attributes"].get("query") for s in with_material
                            if s["span_id"] not in lost and not s["attributes"].get("learnings")]
            extra = {"deep_steps": len(steps), "deep_steps_with_material": len(with_material),
                     "deep_steps_failed": len(lost),
                     "deep_steps_material_but_no_learnings": no_learnings}
        return self.result(rounded(completed / planned), planned=planned, delivered=delivered,
                           completed=completed, retrieval_delivery=rounded(delivered / planned),
                           per_kind=per_kind, not_delivered=failures,
                           failed_after_retrieval=failed_after, **extra)

    @staticmethod
    def _delivering(archive: RunArchive, d, query: str) -> list[dict]:
        """The spans that executed `query` for `d` and came back with chunks."""
        if d.kind == "plan":
            spans = [s for s in archive.children.get(d.span_id, [])
                     if s["name"] == "sub_query" and s["attributes"].get("query") == query]
            return [s for s in spans if s["attributes"].get("chunk_ids")]
        if d.kind == "deep_level":
            spans = [s for s in archive.children.get(d.span_id, [])
                     if s["name"] == "research" and s["attributes"].get("query") == query]
        else:  # subtopics
            spans = [s for s in archive.spans
                     if s["name"] == "research" and s["attributes"].get("query") == query
                     and s["attributes"].get("parent_query")]
        return [s for s in spans if archive.subtree_chunk_ids(s["span_id"])]


def _number(x) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None
