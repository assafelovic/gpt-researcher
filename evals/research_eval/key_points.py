"""
Per-question key points: the K aspects a good answer must cover.
-----------------------------------------------------------------
Generated once per question and shared by every run of it (decomposition
coverage, material coverage, comprehensiveness). Each key point is an aspect
with 2-4 sub-points: the aspect is the unit that is scored, the sub-points
show the judge what it includes. The method (key_points_layered) was chosen
by comparison with four others (key_points_methods.py). Lookup order:

  1. a frozen file `<key_points_dir>/<question_id>.json`
     ({"aspects": [{"aspect": ..., "sub_points": [...]}]}, or the older
     {"key_points": [...]} without sub-points), versioned with the dataset;
  2. the SQLite cache, keyed by question_id + prompt version + judge model;
  3. one judge call, whose result is cached.

Writing the frozen files (one judge call per question, prints the lists):

    python -m evals.research_eval.key_points --write DIR [--questions FILE] [--cache PATH]
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from .cache import stable_hash
from .prompts import KEY_POINTS_LAYERED as KEY_POINTS

if TYPE_CHECKING:
    from .archive import RunArchive
    from .metrics.base import ScoringContext


def parse_key_points(data) -> tuple[list[str], list[list[str]]]:
    """(aspects, sub-points per aspect) from a judge reply or a frozen file."""
    if not isinstance(data, dict):
        return [], []
    points, subs = [], []
    for a in data.get("aspects") or []:
        name = str(a.get("aspect", "")).strip() if isinstance(a, dict) else ""
        if name:
            points.append(name)
            subs.append([str(s).strip() for s in a.get("sub_points") or [] if str(s).strip()])
    for p in data.get("key_points") or [] if not points else []:
        if str(p).strip():
            points.append(str(p).strip())
            subs.append([])
    return points, subs


def render_key_points(points: list[str], provenance: dict) -> str:
    """Numbered key points, each followed by the sub-points it includes."""
    subs = provenance.get("sub_points") or []
    lines = []
    for i, p in enumerate(points, 1):
        lines.append(f"{i}. {p}")
        if i <= len(subs) and subs[i - 1]:
            lines.append("   includes: " + "; ".join(subs[i - 1]))
    return "\n".join(lines)


async def get_key_points(archive: "RunArchive", ctx: "ScoringContext") -> tuple[list[str] | None, dict]:
    """Returns (key_points or None, provenance); provenance["sub_points"] runs parallel to the points."""
    qid = archive.question_id or "q-" + stable_hash(archive.query)[:12]
    memo_key = ("key_points", qid)
    if memo_key in ctx._memo:
        return ctx._memo[memo_key]

    out: tuple[list[str] | None, dict]
    frozen = ctx.key_points_dir / f"{qid}.json" if ctx.key_points_dir else None
    if frozen is not None and frozen.exists():
        points, subs = parse_key_points(json.loads(frozen.read_text(encoding="utf-8")))
        out = (points or None, {"source": "frozen", "path": str(frozen), "sub_points": subs})
    elif ctx.judge is None:
        out = (None, {"source": "unavailable", "reason": "no frozen key points and no judge"})
    else:
        key = stable_hash(qid, KEY_POINTS.id, KEY_POINTS.version, ctx.judge.model)
        cached = ctx.cache.get("question", key)
        if cached is not None:
            points, subs = parse_key_points(cached)
            out = (points, {"source": "cache", "prompt_version": KEY_POINTS.version,
                            "judge_model": ctx.judge.model, "sub_points": subs})
        else:
            resp = await ctx.judge.ask(KEY_POINTS.id, KEY_POINTS.version,
                                       KEY_POINTS.render(question=archive.query))
            points, subs = parse_key_points(resp.parsed)
            if points:
                if not resp.dry:
                    ctx.cache.put("question", key, {"aspects": [
                        {"aspect": p, "sub_points": s} for p, s in zip(points, subs)]})
                out = (points, {"source": "judge", "prompt_version": KEY_POINTS.version,
                                "judge_model": ctx.judge.model, "cache_hit": resp.cache_hit,
                                "sub_points": subs})
            else:
                out = (None, {"source": "failed", "error": resp.error or "empty key point list"})
    ctx._memo[memo_key] = out
    return out


async def write_frozen(argv: list[str] | None = None) -> int:
    import argparse
    from pathlib import Path

    from .cache import DEFAULT_CACHE_PATH, EvalCache
    from .judge import Judge

    ap = argparse.ArgumentParser(description="Write frozen key points, one judge call per question.")
    ap.add_argument("--write", required=True, help="directory for <question_id>.json")
    ap.add_argument("--questions", default=str(Path(__file__).parent / "dataset" / "questions_v0.jsonl"))
    ap.add_argument("--cache", default=str(DEFAULT_CACHE_PATH))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    from dotenv import load_dotenv
    load_dotenv()
    cache = EvalCache(args.cache)
    judge = Judge(cache, dry_run=args.dry_run)
    out = Path(args.write)
    out.mkdir(parents=True, exist_ok=True)
    for line in Path(args.questions).read_text().splitlines():
        if not line.strip():
            continue
        q = json.loads(line)
        qid, text = q.get("id") or q.get("question_id"), q.get("query") or q.get("question")
        r = await judge.ask(KEY_POINTS.id, KEY_POINTS.version, KEY_POINTS.render(question=text))
        points, subs = parse_key_points(r.parsed)
        doc = {"prompt": f"{KEY_POINTS.id} v{KEY_POINTS.version}", "judge_model": judge.model,
               "aspects": [{"aspect": p, "sub_points": s} for p, s in zip(points, subs)]}
        if not args.dry_run:
            (out / f"{qid}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
        print(f"== {qid}\n" + render_key_points(points, {"sub_points": subs}))
    u = judge.usage()
    print(f"\n== judge {u['model']}: {u['calls']} calls ({u['cache_hits']} cache hits)")
    cache.close()
    return 0


if __name__ == "__main__":
    import asyncio
    raise SystemExit(asyncio.run(write_frozen()))
