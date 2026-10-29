"""
Score frozen run archives. Never runs the agent.

Usage:
    python -m evals.research_eval.score evals/research_eval/runs/questions_v0/*.json
    python -m evals.research_eval.score RUN.json --rules-only        # zero-cost metrics only
    python -m evals.research_eval.score RUN.json --metrics plan_adherence,source_diversity
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


async def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("archives", nargs="+")
    ap.add_argument("--metrics", default="", help="comma-separated metric names (default: all)")
    ap.add_argument("--rules-only", action="store_true", help="skip judge and embedding metrics")
    ap.add_argument("--cache", default=str(DEFAULT_CACHE_PATH))
    ap.add_argument("--results-dir", default=str(RESULTS_DIR))
    ap.add_argument("--concurrency", type=int, default=4)
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
                         judge=Judge(cache) if needs_llm else None,
                         embedder=Embedder(cache) if needs_emb else None,
                         key_points_dir=KEY_POINTS_DIR,
                         max_concurrency=args.concurrency)
    for path in args.archives:
        archive = RunArchive.load(path)
        record = await score_archive(archive, metrics, ctx)
        out = save_results(record, args.results_dir)
        print(f"\n== {archive.run_id}  (scorer {record['scorer_version']})")
        for name, value, note in summary_rows(record):
            print(f"   {name:<28} {value:>7}  {note}")
        print(f"   -> {out}")
    cache.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
