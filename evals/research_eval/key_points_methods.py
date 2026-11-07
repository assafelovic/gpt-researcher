"""
Compare ways of writing a question's key points, and keep the most complete.
----------------------------------------------------------------------------
The key points are the denominator of decomposition_coverage,
material_coverage and comprehensiveness, so the method that writes them is
chosen by comparison, not by editing its output. Each method is run twice
per question (cache keys apart), so its stability can be read too:

  current     the key_points prompt, one call
  structured  key_points_structured: what the question asks first, then the
              aspects; one aspect per point, nothing about the report
  consensus   the key_points prompt asked SAMPLES times; the judge groups
              the points by meaning and the groups found in a majority of
              the samples are kept
  layered     key_points_layered: 4-6 aspects with 2-4 sub-points each (the
              aspects are the key points; the sub-points are reported)

Comparison, per question: every list of every method goes into one pool,
which the judge groups by aspect (key_points_merge). An aspect named by at
least POOL_SUPPORT lists is a pool aspect. Per method run:

  coverage     pool aspects its list names / pool aspects
  overlap      pool aspects its list names more than once
  about_report its points the judge marks as about the report itself
  stability    Jaccard of the pool aspects named by its two runs

No report or run archive is read: the pool comes from the methods, not from
what the agent wrote. Usage (no scores are written; prints and saves JSON):

    python -m evals.research_eval.key_points_methods --out DIR [--dry-run] [--max-calls N]
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .cache import DEFAULT_CACHE_PATH, EvalCache
from .judge import Judge
from .prompts import KEY_POINTS, KEY_POINTS_LAYERED, KEY_POINTS_MERGE, KEY_POINTS_STRUCTURED

QUESTIONS = Path(__file__).parent / "dataset" / "questions_v0.jsonl"
METHODS = ("current", "structured", "consensus", "layered")
RUNS = 2
SAMPLES = 5
POOL_SUPPORT = 2


def _points(parsed, field="key_points") -> list[str]:
    if not isinstance(parsed, dict):
        return []
    return [str(p).strip() for p in parsed.get(field) or [] if str(p).strip()]


async def merge(judge: Judge, question: str, lists: list[list[str]], tag: str) -> list[dict]:
    """Groups of point ids ("L<list>.<point>", 1-based) by aspect."""
    text = "\n\n".join(f"List {i}:\n" + "\n".join(f"L{i}.{j} {p}" for j, p in enumerate(ps, 1))
                       for i, ps in enumerate(lists, 1))
    r = await judge.ask(KEY_POINTS_MERGE.id, KEY_POINTS_MERGE.version,
                        KEY_POINTS_MERGE.render(question=question, lists=text), merge=tag)
    groups = r.parsed.get("groups") if isinstance(r.parsed, dict) else None
    return [g for g in groups or [] if isinstance(g, dict)]


def _list_of(pid: str) -> int | None:
    try:
        return int(str(pid).split(".")[0].lstrip("L"))
    except ValueError:
        return None


async def run_method(judge: Judge, method: str, question: str, run: int) -> dict:
    if method == "current":
        r = await judge.ask(KEY_POINTS.id, KEY_POINTS.version, KEY_POINTS.render(question=question),
                            **({"vote": run} if run else {}))
        return {"key_points": _points(r.parsed)}
    if method == "structured":
        r = await judge.ask(KEY_POINTS_STRUCTURED.id, KEY_POINTS_STRUCTURED.version,
                            KEY_POINTS_STRUCTURED.render(question=question), vote=run)
        return {"key_points": _points(r.parsed), "asked": _points(r.parsed, "asked")}
    if method == "layered":
        r = await judge.ask(KEY_POINTS_LAYERED.id, KEY_POINTS_LAYERED.version,
                            KEY_POINTS_LAYERED.render(question=question), vote=run)
        aspects = [a for a in (r.parsed or {}).get("aspects") or [] if isinstance(a, dict)] \
            if isinstance(r.parsed, dict) else []
        return {"key_points": [str(a.get("aspect", "")).strip() for a in aspects if a.get("aspect")],
                "sub_points": {str(a.get("aspect", "")).strip(): a.get("sub_points") or [] for a in aspects}}
    # consensus: SAMPLES calls of the current prompt, grouped, majority kept
    samples = await asyncio.gather(*(
        judge.ask(KEY_POINTS.id, KEY_POINTS.version, KEY_POINTS.render(question=question),
                  vote=f"consensus{run}.{k}") for k in range(SAMPLES)))
    lists = [_points(s.parsed) for s in samples]
    groups = await merge(judge, question, lists, f"consensus{run}")
    kept = []
    for g in groups:
        support = {_list_of(p) for p in g.get("points") or []} - {None}
        if len(support) > SAMPLES / 2 and not g.get("about_report"):
            kept.append(str(g.get("name", "")).strip())
    return {"key_points": [k for k in kept if k], "samples": lists}


async def compare_question(judge: Judge, qid: str, question: str) -> dict:
    out: dict[str, list[dict]] = {m: [] for m in METHODS}
    runs = await asyncio.gather(*(run_method(judge, m, question, r) for m in METHODS for r in range(RUNS)))
    lists, owner = [], []
    for (m, r), res in zip(((m, r) for m in METHODS for r in range(RUNS)), runs):
        out[m].append(res)
        lists.append(res["key_points"])
        owner.append((m, r))
    groups = await merge(judge, question, lists, "pool")
    point_group = {}
    for gi, g in enumerate(groups):
        for p in g.get("points") or []:
            point_group[str(p)] = gi
    support = {gi: {_list_of(p) for p in g.get("points") or []} - {None} for gi, g in enumerate(groups)}
    pool = [gi for gi, s in support.items() if len(s) >= POOL_SUPPORT and not groups[gi].get("about_report")]
    stats = {}
    for li, ((m, r), ps) in enumerate(zip(owner, lists), 1):
        named = [point_group.get(f"L{li}.{j}") for j in range(1, len(ps) + 1)]
        hit = {g for g in named if g in pool}
        stats.setdefault(m, []).append({
            "points": len(ps), "coverage": round(len(hit) / len(pool), 3) if pool else None,
            "overlap": sum(1 for g in set(named) if g is not None and named.count(g) > 1),
            "about_report": sum(1 for g in named if g is not None and groups[g].get("about_report")),
            "unmatched": sum(1 for g in named if g is None), "aspects": sorted(hit)})
    for m, rs in stats.items():
        a, b = set(rs[0]["aspects"]), set(rs[1]["aspects"])
        for x in rs:
            x["stability"] = round(len(a & b) / len(a | b), 3) if a | b else None
    return {"question_id": qid, "question": question, "methods": out, "stats": stats,
            "pool": [{"id": gi, "name": groups[gi].get("name"), "lists": len(support[gi])} for gi in pool],
            "groups": groups}


async def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default=str(DEFAULT_CACHE_PATH))
    ap.add_argument("--questions", default=str(QUESTIONS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-calls", type=int, default=None)
    args = ap.parse_args(argv)
    from dotenv import load_dotenv
    load_dotenv()
    cache = EvalCache(args.cache)
    judge = Judge(cache, max_calls=args.max_calls, dry_run=args.dry_run)
    qs = [json.loads(line) for line in Path(args.questions).read_text().splitlines() if line.strip()]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for q in qs:
        qid, text = q.get("id") or q.get("question_id"), q.get("query") or q.get("question")
        res = await compare_question(judge, qid, text)
        results.append(res)
        if not args.dry_run:
            (out / f"{qid}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
        print(f"== {qid}: pool {len(res['pool'])} aspects")
        for m, rs in res["stats"].items():
            print(f"   {m:<11} " + " | ".join(
                f"n={x['points']} cov={x['coverage']} overlap={x['overlap']} report={x['about_report']}"
                for x in rs) + f" | stability={rs[0]['stability']}")
    u = judge.usage()
    print(f"\n== judge {u['model']}: {u['calls']} calls ({u['cache_hits']} cache hits)"
          + ("" if args.dry_run else f", {u['input_tokens']} input / {u['output_tokens']} output tokens"))
    cache.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
