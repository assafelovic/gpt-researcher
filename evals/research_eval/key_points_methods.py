"""
Compare ways of writing a question's key points, and keep the most complete.
----------------------------------------------------------------------------
The key points are the denominator of decomposition_coverage,
material_coverage and comprehensiveness, so the method that writes them is
chosen by comparison, not by editing its output. Each method is run twice
per question (cache keys apart), so its stability can be read too:

  current      the key_points prompt, one call
  structured   key_points_structured: what the question asks first, then
               the aspects; one aspect per point, nothing about the report
  consensus    the key_points prompt asked SAMPLES times; the judge groups
               the points and the groups found in a majority are kept
  layered      key_points_layered: 4-6 aspects with 2-4 sub-points each
  consensus+   the consensus aspects, each described by 2-4 sub-points
               (key_points_describe)
  layered-merged  DRAFTS layered drafts, then key_points_synthesize writes
               one list from them (key_points.generate_key_points)

The key points are the top level; sub-points describe them (a judge could be
shown them) and count for coverage.

Comparison, per question. The pool: every list of every method, plus two
outlines of an excellent answer written independently (key_points_outline),
grouped by the judge into single things (key_points_merge v2: a point that
names three things goes in three groups). A thing named by at least
POOL_SUPPORT lists is a pool thing. Per method run:

  coverage          pool things its points (and sub-points) name / pool things
  outline_coverage  the same over the pool things an outline names: less
                    circular, since the outlines are not key point lists
  compound          mean number of things per top-level point (1 = single)
  overlap           things named by two or more of its top-level points
  about_report      top-level points the judge marks as about the report
  stability         Jaccard of the pool things named by its two runs

No report or run archive is read. Usage (prints and saves JSON, no scores):

    python -m evals.research_eval.key_points_methods --out DIR [--dry-run] [--max-calls N]
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .cache import DEFAULT_CACHE_PATH, EvalCache
from .judge import Judge
from .key_points import generate_key_points
from .prompts import (KEY_POINTS, KEY_POINTS_DESCRIBE, KEY_POINTS_LAYERED, KEY_POINTS_MERGE,
                      KEY_POINTS_OUTLINE, KEY_POINTS_STRUCTURED)

QUESTIONS = Path(__file__).parent / "dataset" / "questions_v0.jsonl"
METHODS = ("current", "structured", "consensus", "layered", "consensus+", "layered-merged")
RUNS = 2
SAMPLES = 5
POOL_SUPPORT = 2
DRAFTS = 3


def _points(parsed, field="key_points") -> list[str]:
    if not isinstance(parsed, dict):
        return []
    return [str(p).strip() for p in parsed.get(field) or [] if str(p).strip()]


def _aspects(parsed) -> list[dict]:
    items = parsed.get("aspects") if isinstance(parsed, dict) else None
    return [{"aspect": str(a.get("aspect", "")).strip(),
             "sub_points": [str(s).strip() for s in a.get("sub_points") or [] if str(s).strip()]}
            for a in items or [] if isinstance(a, dict) and str(a.get("aspect", "")).strip()]


async def merge(judge: Judge, question: str, lists: list[list[str]], tag: str) -> list[dict]:
    """Groups of point ids ("L<list>.<point>", 1-based); a point may be in several."""
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


async def consensus(judge: Judge, question: str, run: int) -> dict:
    samples = await asyncio.gather(*(
        judge.ask(KEY_POINTS.id, KEY_POINTS.version, KEY_POINTS.render(question=question),
                  vote=f"consensus{run}.{k}") for k in range(SAMPLES)))
    lists = [_points(s.parsed) for s in samples]
    groups = await merge(judge, question, lists, f"consensus{run}")
    kept = []
    for g in groups:
        support = {_list_of(p) for p in g.get("points") or []} - {None}
        name = str(g.get("name", "")).strip()
        if name and len(support) > SAMPLES / 2 and not g.get("about_report"):
            kept.append(name)
    return {"key_points": kept, "samples": lists}


async def run_method(judge: Judge, method: str, question: str, run: int, memo: dict) -> dict:
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
        aspects = _aspects(r.parsed)
        return {"key_points": [a["aspect"] for a in aspects],
                "sub_points": {a["aspect"]: a["sub_points"] for a in aspects}}
    if method == "layered-merged":
        points, subs, _ = await generate_key_points(judge, question, DRAFTS, vote=run)
        return {"key_points": points, "sub_points": dict(zip(points, subs))}
    if run not in memo:
        memo[run] = asyncio.ensure_future(consensus(judge, question, run))
    base = await memo[run]
    if method == "consensus":
        return base
    r = await judge.ask(KEY_POINTS_DESCRIBE.id, KEY_POINTS_DESCRIBE.version, KEY_POINTS_DESCRIBE.render(
        question=question, key_points="\n".join(f"{i}. {p}" for i, p in enumerate(base["key_points"], 1))),
        vote=run)
    subs = {a["aspect"]: a["sub_points"] for a in _aspects(r.parsed)}
    return {"key_points": base["key_points"],
            "sub_points": {k: subs.get(k, []) for k in base["key_points"]}}


async def outline(judge: Judge, question: str, run: int) -> list[str]:
    r = await judge.ask(KEY_POINTS_OUTLINE.id, KEY_POINTS_OUTLINE.version,
                        KEY_POINTS_OUTLINE.render(question=question), vote=run)
    secs = r.parsed.get("sections") if isinstance(r.parsed, dict) else None
    return [str(p).strip() for s in secs or [] if isinstance(s, dict)
            for p in s.get("points") or [] if str(p).strip()]


async def compare_question(judge: Judge, qid: str, question: str) -> dict:
    memo: dict = {}
    order = [(m, r) for m in METHODS for r in range(RUNS)]
    runs = await asyncio.gather(*(run_method(judge, m, question, r, memo) for m, r in order))
    outlines = await asyncio.gather(*(outline(judge, question, r) for r in range(RUNS)))
    out: dict[str, list[dict]] = {m: [] for m in METHODS}
    lists, tops = [], []
    for (m, _), res in zip(order, runs):
        out[m].append(res)
        subs = [s for k in res["key_points"] for s in (res.get("sub_points") or {}).get(k, [])]
        lists.append(res["key_points"] + subs)
        tops.append(len(res["key_points"]))
    first_outline = len(lists) + 1
    lists += outlines
    groups = await merge(judge, question, lists, "pool")
    groups_of: dict[str, set[int]] = {}
    for gi, g in enumerate(groups):
        for p in g.get("points") or []:
            groups_of.setdefault(str(p), set()).add(gi)
    support = {gi: {_list_of(p) for p in g.get("points") or []} - {None} for gi, g in enumerate(groups)}
    pool = {gi for gi, s in support.items() if len(s) >= POOL_SUPPORT and not groups[gi].get("about_report")}
    in_outline = {gi for gi in pool if any(li >= first_outline for li in support[gi])}
    stats: dict[str, list[dict]] = {}
    for li, ((m, _), ps, n_top) in enumerate(zip(order, lists, tops), 1):
        per_point = [groups_of.get(f"L{li}.{j}", set()) for j in range(1, len(ps) + 1)]
        hit = set().union(*per_point) & pool if per_point else set()
        top = per_point[:n_top]
        counts = {}
        for gs in top:
            for g in gs:
                counts[g] = counts.get(g, 0) + 1
        stats.setdefault(m, []).append({
            "points": n_top, "sub_points": len(ps) - n_top,
            "coverage": round(len(hit) / len(pool), 3) if pool else None,
            "outline_coverage": round(len(hit & in_outline) / len(in_outline), 3) if in_outline else None,
            "compound": round(sum(len(gs) for gs in top) / n_top, 2) if n_top else None,
            "overlap": sum(1 for g, c in counts.items() if c > 1 and g in pool),
            "about_report": sum(1 for gs in top if any(groups[g].get("about_report") for g in gs)),
            "things": sorted(hit)})
    for rs in stats.values():
        a, b = set(rs[0]["things"]), set(rs[1]["things"])
        for x in rs:
            x["stability"] = round(len(a & b) / len(a | b), 3) if a | b else None
    return {"question_id": qid, "question": question, "methods": out, "outlines": outlines,
            "stats": stats,
            "pool": [{"id": gi, "name": groups[gi].get("name"), "lists": len(support[gi]),
                      "in_outline": gi in in_outline} for gi in sorted(pool)],
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
                f"n={x['points']}+{x['sub_points']} cov={x['coverage']} outline={x['outline_coverage']} "
                f"compound={x['compound']} overlap={x['overlap']} report={x['about_report']}"
                for x in rs) + f" | stability={rs[0]['stability']}")
    u = judge.usage()
    print(f"\n== judge {u['model']}: {u['calls']} calls ({u['cache_hits']} cache hits)"
          + ("" if args.dry_run else f", {u['input_tokens']} input / {u['output_tokens']} output tokens"))
    cache.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
