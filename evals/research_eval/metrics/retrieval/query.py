"""
A. Query metrics: what the agent decided to search for.
"""

from __future__ import annotations

from itertools import combinations

from ...archive import RunArchive
from ...judge import cosine
from ...key_points import get_key_points, render_key_points
from ...prompts import DECOMPOSITION_COVERAGE, KEY_POINTS_LAYERED, SUBQUERY_REDUNDANCY, TREE_QUALITY
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
    version = "6"           # 3: deep clarifying questions are not sub-queries; 4: "aimed at" from the query-quality skill;
                            # 5: the skill rewritten short, with shared principles;
                            # 6: layered key points, the judge sees each point's sub-points
    uses_llm = True
    prompts = (KEY_POINTS_LAYERED, DECOMPOSITION_COVERAGE)
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
            key_points=render_key_points(points, provenance),
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
    new material. Any two nodes may repeat each other, at any layer and in
    any branch, except a node and the nodes it was split from (its ancestors,
    `RunArchive.query_node_ancestors`): those overlap by design.

    With a judge, pair by pair: code lists the candidate pairs and the judge
    sees one pair per call (the research question and the two queries, never
    the tree), says what each asks that the other does not, and whether the
    later one repeats the earlier (the same facts would answer both).
    Candidates: for each node, the CANDIDATES other nodes (not its ancestors
    or descendants) with the highest symmetric BM25-weighted word overlap,
    IDF over all nodes, however low (v12 had a 0.15 floor, which dropped
    rewordings in synonyms: "top vendors" / "leading companies" at 0.04). Judging all
    pairs would cost n^2/2 calls (200-600 in a deep tree); a repeat in other
    words still shares the words of its subject. `details.pairs` /
    `details.all_pairs` say how many were judged. Repeats chain into groups;
    in each group the node searched first is the original and the rest are
    duplicates.

        value = duplicate nodes / all nodes

    `details.per_layer` and `details.per_kind` (branch / leaf) give the share
    by the duplicate's layer and kind; `details.same_layer` and
    `details.same_parent` count the duplicates whose original sits on the
    same layer / has the same parent. A pair whose call failed is listed in
    `details.unanswered` (its later query) and counts as not a repeat.
    `redundancy_votes` > 1 asks each pair that many times and takes the
    majority (`details.unstable` lists split pairs).

    Without a judge (`details.method` = "lexical"): sibling pairs whose
    symmetric BM25-weighted term overlap reaches the threshold, IDF over the
    sibling group. Kept as a fallback only: with three or four siblings the
    group IDF gives shared words so little weight that near-duplicates score
    well under the threshold, and branches are never compared.
    """

    name, category = "subquery_redundancy", "retrieval.query_quality"
    version = "13"          # 4: only a reworded request for the same facts; 5: sub-queries only;
                            # 6: own call per layer over every node; 7: whole tree but ancestors, one call;
                            # 8: overlaps beside repeats (too broad, dropped); 9: majority of VOTES calls;
                            # 10: "repeat" from the query-quality skill, with examples;
                            # 11: the skill rewritten short, with shared principles;
                            # 12: code-picked candidate pairs, one pair per call; 13: no overlap floor
    higher_is_better = False
    uses_llm = True         # the lexical fallback only runs when no judge is configured at all
    prompts = (SUBQUERY_REDUNDANCY,)
    DEFAULT_THRESHOLD = 0.6
    VOTES = 1
    CANDIDATES = 3          # most similar other nodes per node
    MIN_OVERLAP = 0.0

    @classmethod
    def candidate_pairs(cls, archive: RunArchive, k: int | None = None,
                        min_overlap: float | None = None) -> tuple[list[tuple[int, int]], int]:
        """(i, j) node numbers (1-based, i searched first) to judge, and the
        number of comparable pairs in all."""
        nodes = archive.query_nodes
        k = cls.CANDIDATES if k is None else k
        floor = cls.MIN_OVERLAP if min_overlap is None else min_overlap
        index = {n.span_id: i for i, n in enumerate(nodes, 1)}
        above = {i: {index[a] for a in archive.query_node_ancestors[n.span_id]} for i, n in enumerate(nodes, 1)}
        related = lambda i, j: i in above[j] or j in above[i]
        texts = [" ".join(n.query.split()) for n in nodes]
        idf = idf_table(texts)
        comparable = [(i, j) for i, j in combinations(range(1, len(nodes) + 1), 2) if not related(i, j)]
        sim = {(i, j): symmetric_overlap(texts[i - 1], texts[j - 1], idf) for i, j in comparable}
        picked = set()
        for x in range(1, len(nodes) + 1):
            mine = sorted(((s, pair) for pair, s in sim.items() if x in pair and s >= floor),
                          key=lambda e: (-e[0], e[1]))
            picked.update(pair for _, pair in mine[:k])
        return sorted(picked), len(comparable)

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self._lexical(archive, ctx)
        nodes = archive.query_nodes
        if not nodes:
            return self.skip("no searched query below the run's question")
        if len(nodes) == 1:
            return self.result(0.0, method="judge_pairs", nodes=1, duplicates=0, reason="one node")
        pairs, comparable = self.candidate_pairs(
            archive, int(ctx.option("redundancy_candidates", self.CANDIDATES)),
            float(ctx.option("redundancy_min_overlap", self.MIN_OVERLAP)))
        votes = max(1, int(ctx.option("redundancy_votes", self.VOTES)))
        question = archive.query.strip()

        async def ask(i, j, k):
            prompt = SUBQUERY_REDUNDANCY.render(question=question, query_a=" ".join(nodes[i - 1].query.split()),
                                                query_b=" ".join(nodes[j - 1].query.split()))
            # The first call keeps the plain cache key, so a single-call verdict is reused.
            return (i, j), await ctx.judge.ask(SUBQUERY_REDUNDANCY.id, SUBQUERY_REDUNDANCY.version, prompt,
                                               **({"vote": k} if k else {}))

        answers = await ctx.gather(ask(i, j, k) for i, j in pairs for k in range(votes))
        replies = [r for _, r in answers]
        ballots: dict[tuple[int, int], list[dict]] = {}
        for pair, r in answers:
            if isinstance(r.parsed, dict) and isinstance(r.parsed.get("repeat"), bool):
                ballots.setdefault(pair, []).append(r.parsed)
        if pairs and not ballots:
            res = self.skip("judge call failed", errors=[r.error for r in replies][:5],
                            raw=(replies[0].raw or "")[:300])
            res.llm = self.llm_record(ctx, replies)
            return res

        links, unstable = {}, []
        for (i, j), bs in sorted(ballots.items()):
            yes = [b for b in bs if b["repeat"]]
            counted = len(yes) > len(bs) / 2
            if yes and len(yes) < len(bs):
                unstable.append({"query": nodes[j - 1].query, "repeats": nodes[i - 1].query,
                                 "marks": len(yes), "replies": len(bs), "counted": counted})
            if counted and j not in links:      # the earliest original it repeats
                b = yes[0]
                links[j] = (i, f"only in A: {b.get('only_in_a', '')}; only in B: {b.get('only_in_b', '')}")
        # Groups of repeats; the node searched first is each group's original.
        group = list(range(len(nodes) + 1))
        find = lambda x: x if group[x] == x else find(group[x])
        for j, (i, _) in links.items():
            a, b = sorted((find(i), find(j)))
            group[b] = a
        index = {n.span_id: i for i, n in enumerate(nodes, 1)}
        above = {i: {index[a] for a in archive.query_node_ancestors[n.span_id]} for i, n in enumerate(nodes, 1)}
        related = lambda i, j: i in above[j] or j in above[i]
        members: dict[int, list[int]] = {}
        for i in range(1, len(nodes) + 1):
            members.setdefault(find(i), []).append(i)
        duplicates = []
        for x, n in enumerate(nodes, 1):
            if find(x) == x:
                continue
            o_i, evidence = links.get(x, (None, ""))
            if o_i is None:                     # in a group only through another node's link
                o_i = next((k for k in members[find(x)] if k != x and not related(x, k)), find(x))
            o = nodes[o_i - 1]
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
            rounded(len(dup_ids) / len(nodes)), method="judge_pairs", nodes=len(nodes),
            duplicates=len(dup_ids), same_layer=sum(d["same_layer"] for d in duplicates),
            same_parent=sum(d["same_parent"] for d in duplicates),
            per_layer=by("layer"), per_kind=by("kind"), votes=votes,
            pairs=len(pairs), all_pairs=comparable, repeat_pairs=sum(1 for bs in ballots.values()
                                                                     if sum(b["repeat"] for b in bs) > len(bs) / 2),
            not_unique=duplicates, unstable=unstable,
            unanswered=list(dict.fromkeys(nodes[j - 1].query for i, j in pairs if (i, j) not in ballots)))
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
    """Depth of the search tree: does each split take a step away from its
    parent, or only restate it or drift away?

    Breadth over the question is decomposition_coverage (do the sub-queries
    reach its key points) and waste is subquery_redundancy; this metric looks
    at each parent -> child step on its own. One call per decomposition that
    was searched (deep research's clarifying questions are left out: they are
    folded into one query, never searched). The judge sees the path from the
    question down to the parent (`RunArchive.query_path`) and, for each child,
    says whether it takes a step from the parent or has a problem that leaves
    it with none (restated, drifted). Deeper, wider and more specific are the
    directions a step can take, given as hints; the judge names every one a
    child takes, but any step is a good split.

        child score  = 1 when it takes a step, 0 when restated or drifted
        parent score = mean child score
        value        = mean parent score

    One overall score, not one per direction: a child can go both deeper and
    wider, and a one-level default run is not marked down for its mode.
    A deeper deep-research level follows a search step whose findings
    (learnings) the archive records; the judge is shown them and names the
    findings each child follows up (`details.builds_on_findings`, a
    diagnostic). `details.directions` and `details.problems` count the
    judge's labels, for reading the scores, not as scores of their own. The
    definitions come from the query-quality skill (prompts/query-quality/SKILL.md).
    """

    name, category = "decomposition_tree_quality", "retrieval.query_quality"
    version = "9"           # 3: the judge sees the root-to-parent path; 4: per-child checks + aspect coverage;
                            # 5: check and aspect definitions from the query-quality skill, with examples;
                            # 6: the parent's aspects are fixed before the children are shown;
                            # 7: the skill rewritten short, with shared principles;
                            # 8: depth only: one relation per child, findings in deep research, no coverage;
                            # 9: one overall score per child (a step or not); deeper, wider, specific are hints
    uses_llm = True
    prompts = (TREE_QUALITY,)
    DIRECTIONS = ("deeper", "wider", "specific")
    PROBLEMS = ("restated", "drifted")

    @classmethod
    def child_score(cls, kid: dict) -> float:
        return 1.0 if kid["problem"] == "none" and kid["directions"] else 0.0

    async def score(self, archive: RunArchive, ctx: ScoringContext) -> MetricResult:
        if ctx.judge is None:
            return self.skip("no judge configured")
        decs = [d for d in archive.decompositions if d.child_queries and d.kind != "deep_plan"]
        if not decs:
            return self.skip("no decompositions")
        question = archive.query.strip()

        async def judge_one(d):
            path = archive.query_path(d.span_id)
            if path[-1] != d.parent_query.strip():
                path.append(d.parent_query.strip())
            findings = self.findings(archive, d)
            prompt = TREE_QUALITY.render(
                question=question,
                path="\n".join(f"{i}. {self._short(q)}" for i, q in enumerate(path)),
                parent=d.parent_query.strip(),
                findings="\n".join(f"{i}. {f}" for i, f in enumerate(findings, 1)) or "none",
                children="\n".join(f"{i}. {c}" for i, c in enumerate(d.child_queries, 1)))
            return d, findings, await ctx.judge.ask(TREE_QUALITY.id, TREE_QUALITY.version, prompt)

        results = await ctx.gather(judge_one(d) for d in decs)
        per_parent, scores, verdicts, weak, after_findings = [], [], [], [], []
        for d, findings, r in results:
            parsed = r.parsed if isinstance(r.parsed, dict) else {}
            n = len(d.child_queries)
            kids = {}
            for e in parsed.get("children") or []:
                try:
                    i = int(e["child"])
                except (KeyError, TypeError, ValueError):
                    continue
                problem = str(e.get("problem") or "").strip().lower()
                dirs = e.get("directions") if isinstance(e.get("directions"), list) else []
                dirs = sorted({str(x).strip().lower() for x in dirs} & set(self.DIRECTIONS),
                              key=self.DIRECTIONS.index)
                if not 1 <= i <= n or problem not in ("none", *self.PROBLEMS):
                    continue
                if problem != "none":
                    dirs = []
                kid = {"problem": problem, "directions": dirs, "left_out": str(e.get("left_out") or ""),
                       "evidence": str(e.get("evidence") or ""),
                       "builds_on": _child_numbers(e.get("builds_on"), len(findings))}
                kid["score"] = self.child_score(kid)
                kids[i] = kid
            score = sum(k["score"] for k in kids.values()) / len(kids) if kids else None
            if score is not None:
                scores.append(score)
                verdicts += kids.values()
                if findings:
                    after_findings += kids.values()
                weak += [{"parent": d.parent_query.strip()[:200], "child": d.child_queries[i - 1],
                          "problem": k["problem"], "evidence": k["evidence"]}
                         for i, k in sorted(kids.items()) if k["score"] == 0]
            per_parent.append({"span_id": d.span_id, "kind": d.kind, "parent": d.parent_query,
                               "depth": len(archive.query_path(d.span_id)) - 1, "n_children": n,
                               "score": rounded(score), "findings": findings,
                               "children": [{"child": d.child_queries[i - 1], **kids[i]} for i in sorted(kids)],
                               "unanswered_children": n - len(kids), "error": r.error})
        count = lambda pred: sum(pred(v) for v in verdicts)
        res = self.result(
            rounded(sum(scores) / len(scores)) if scores else None, per_parent=per_parent,
            scored_parents=len(scores), children=len(verdicts),
            directions={x: count(lambda v: x in v["directions"]) for x in self.DIRECTIONS},
            problems={x: count(lambda v: v["problem"] == x) for x in self.PROBLEMS},
            builds_on_findings=rounded(sum(bool(v["builds_on"]) for v in after_findings) / len(after_findings))
            if after_findings else None,
            children_after_findings=len(after_findings), weak_children=weak)
        if not scores:
            res.skipped = "every judge call failed"
        res.llm = self.llm_record(ctx, [r for _, _, r in results])
        return res

    @staticmethod
    def findings(archive: RunArchive, d) -> list[str]:
        """Learnings of the search step a deeper deep-research level follows:
        the level's span hangs under the research branch whose goal and
        follow-ups produced it (capture.py re-parents it)."""
        if d.kind != "deep_level":
            return []
        parent = archive.span_by_id.get(archive.span_by_id[d.span_id].get("parent_id"))
        if parent is None or parent["name"] != "research":
            return []
        return [str(x).strip() for x in parent["attributes"].get("learnings") or [] if str(x).strip()]

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


def _child_numbers(xs, n: int) -> list[int]:
    """Child numbers 1..n from a judge's list ("2" is read as 2), in order, once each."""
    out = []
    for k in xs if isinstance(xs, list) else []:
        if isinstance(k, bool):
            continue
        try:
            k = int(k)
        except (TypeError, ValueError):
            continue
        if 1 <= k <= n and k not in out:
            out.append(k)
    return out


def _number(x) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None
