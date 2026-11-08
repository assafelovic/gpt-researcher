"""
Write the frozen insight/readability rubrics (dataset/rubrics/<question_id>.json).
---------------------------------------------------------------------------------
One quality_rubric call per question, the same call insight and readability
make when no frozen rubric exists. Review the output before copying it into
the dataset.

    python -m evals.research_eval.rubrics --write DIR [--questions FILE] [--cache PATH] [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .cache import DEFAULT_CACHE_PATH, EvalCache
from .judge import Judge
from .prompts import QUALITY_RUBRIC


def render(rubric: dict) -> str:
    lines = []
    for dim in ("insight", "readability"):
        lines.append(f"[{dim}]")
        for c in rubric.get(dim) or []:
            lines.append(f"  {c.get('weight')}  {c.get('criterion')}: {c.get('description')}")
    return "\n".join(lines)


async def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Write frozen rubrics, one judge call per question.")
    ap.add_argument("--write", required=True)
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
        r = await judge.ask(QUALITY_RUBRIC.id, QUALITY_RUBRIC.version, QUALITY_RUBRIC.render(question=text))
        rubric = r.parsed if isinstance(r.parsed, dict) else {}
        if not args.dry_run:
            (out / f"{qid}.json").write_text(json.dumps(rubric, indent=1, ensure_ascii=False) + "\n")
        print(f"== {qid}\n{render(rubric)}")
    u = judge.usage()
    print(f"\n== judge {u['model']}: {u['calls']} calls ({u['cache_hits']} cache hits)"
          + ("" if args.dry_run else f", {u['input_tokens']} input / {u['output_tokens']} output tokens"))
    cache.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
