"""
Score frozen run archives. Never runs the agent.

Usage:
    python -m evals.research_eval.score evals/research_eval/runs/questions_v0/*.json
    python -m evals.research_eval.score RUN.json --rules-only        # zero-cost metrics only
    python -m evals.research_eval.score RUN.json --metrics plan_adherence,source_diversity
    python -m evals.research_eval.score RUNS --dry-run          # count uncached judge calls, call nothing
    python -m evals.research_eval.score RUNS --max-calls 300    # stop calling the judge after 300 calls
    python -m evals.research_eval.score RUNS --judge-salt noise1  # ask the judge again (noise control)
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .archive import RunArchive
from .cache import DEFAULT_CACHE_PATH, EvalCache
from .judge import Embedder, Judge
from .metrics import all_metrics
from .metrics.base import ScoringContext
from .scoring import RESULTS_DIR, save_results, score_archive, summary_rows

KEY_POINTS_DIR = Path(__file__).parent / "dataset" / "key_points"
RUBRICS_DIR = Path(__file__).parent / "dataset" / "rubrics"


async def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("archives", nargs="+")
    ap.add_argument("--metrics", default="", help="comma-separated metric names (default: all)")
    ap.add_argument("--rules-only", action="store_true", help="skip judge and embedding metrics")
    ap.add_argument("--cache", default=str(DEFAULT_CACHE_PATH))
    ap.add_argument("--results-dir", default=str(RESULTS_DIR))
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--score-failed", action="store_true",
                    help="score runs that failed (agent error or no real report) instead of skipping them")
    ap.add_argument("--dry-run", action="store_true",
                    help="call no model and save nothing: count the judge calls the cache does not "
                         "cover (first-pass only: follow-up calls that depend on a verdict are not counted)")
    ap.add_argument("--max-calls", type=int, default=None,
                    help="cap on uncached judge calls; past it, judge metrics are skipped with an error")
    ap.add_argument("--rubrics-dir", default=str(RUBRICS_DIR),
                    help="frozen insight/readability rubrics; 'none' makes the judge write them")
    ap.add_argument("--judge-salt", default="",
                    help="key the judge cache apart so cached verdicts are asked again")
    args = ap.parse_args(argv)

    from dotenv import load_dotenv
    load_dotenv()

    metrics = all_metrics()
    if args.metrics:
        wanted = set(args.metrics.split(","))
        unknown = wanted - {m.name for m in metrics}
        if unknown:
            ap.error(f"unknown metrics: {', '.join(sorted(unknown))}")
        metrics = [m for m in metrics if m.name in wanted]
    if args.rules_only:
        metrics = [m for m in metrics if not (m.uses_llm or m.uses_embeddings)]

    cache = EvalCache(args.cache)
    needs_llm = any(m.uses_llm for m in metrics)
    needs_emb = any(m.uses_embeddings for m in metrics)
    ctx = ScoringContext(cache=cache,
                         judge=Judge(cache, salt=args.judge_salt, max_calls=args.max_calls,
                                     dry_run=args.dry_run) if needs_llm else None,
                         embedder=Embedder(cache) if needs_emb else None,
                         key_points_dir=KEY_POINTS_DIR, rubrics_dir=None if args.rubrics_dir == "none" else Path(args.rubrics_dir),
                         max_concurrency=args.concurrency)
    for path in args.archives:
        archive = RunArchive.load(path)
        before = ctx.judge.calls if ctx.judge else 0
        record = await score_archive(archive, metrics, ctx, score_failed=args.score_failed)
        if args.dry_run:
            print(f"== {archive.run_id}: {(ctx.judge.calls if ctx.judge else 0) - before} uncached judge calls")
            continue
        out = save_results(record, args.results_dir)
        print(f"\n== {archive.run_id}  (scorer {record['scorer_version']})")
        if record["failure"]:
            print(f"   FAILED RUN: {record['failure']}")
        for name, value, note in summary_rows(record):
            print(f"   {name:<28} {value:>7}  {note}")
        print(f"   -> {out}")
    if ctx.judge is not None:
        u = ctx.judge.usage()
        if args.dry_run:
            print(f"\n== dry run, judge {u['model']}: {u['calls']} uncached calls would be made "
                  f"(~{u['prompt_chars'] // 4} input tokens), {u['cache_hits']} cache hits; follow-up "
                  f"requests are counted on a minimal answer (one item per list), so calls that "
                  f"depend on real verdicts, such as claim rechecks, can add more")
        else:
            print(f"\n== judge {u['model']}: {u['calls']} calls ({u['cache_hits']} cache hits), "
                  f"{u['input_tokens']} input / {u['output_tokens']} output tokens (uncached calls)")
            if u["refused"]:
                print(f"== call budget reached: {u['refused']} judge calls were not made; "
                      f"their metrics are skipped")
    cache.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
