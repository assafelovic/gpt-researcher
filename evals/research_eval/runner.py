"""
Runner: question set -> one frozen run archive per (question, mode).
--------------------------------------------------------------------
Runs gpt-researcher with a fixed configuration under RunCapture and writes the
archive. It does not score; see score.py.

Usage:
    python -m evals.research_eval.runner --modes default --limit 2
    python -m evals.research_eval.runner --dataset path/to/questions.jsonl --modes default,detailed,deep
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .archive import build_archive, save_archive
from .capture import RunCapture
from .tracing import Tracer

DATASET = Path(__file__).parent / "dataset" / "questions_v0.jsonl"
RUNS_DIR = Path(__file__).parent / "runs"
MODES = ("default", "detailed", "deep")


def load_questions(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dataset_version(path: str | Path) -> str:
    return Path(path).stem


def agent_commit() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                             text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                               text=True, check=True).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


def run_config(researcher, mode: str, capture: RunCapture) -> dict:
    cfg = researcher.cfg
    return {
        "report_type": researcher.report_type,
        "mode": mode,
        "context_filter": getattr(cfg, "context_filter", None),
        "context_filter_resolved": sorted(capture.context_filters),
        "worker_model": {
            "smart": f"{cfg.smart_llm_provider}:{cfg.smart_llm_model}",
            "fast": f"{cfg.fast_llm_provider}:{cfg.fast_llm_model}",
            "strategic": f"{cfg.strategic_llm_provider}:{cfg.strategic_llm_model}",
        },
        "embedding": f"{cfg.embedding_provider}:{cfg.embedding_model}",
        "retrievers": [r.__name__ for r in researcher.retrievers],
        "max_iterations": getattr(cfg, "max_iterations", None),
        "max_search_results_per_query": getattr(cfg, "max_search_results_per_query", None),
        "breadth": getattr(cfg, "deep_research_breadth", None) if mode == "deep" else None,
        "depth": getattr(cfg, "deep_research_depth", None) if mode == "deep" else None,
    }


async def _research(question: dict, mode: str):
    """Run one question in one mode. Returns (researcher, report markdown)."""
    from gpt_researcher.agent import GPTResearcher
    from gpt_researcher.utils.enum import ReportSource, ReportType, Tone

    query = question["question"]
    if mode == "detailed":
        from backend.report_type import DetailedReport
        detailed = DetailedReport(query=query, report_type=ReportType.ResearchReport.value,
                                  report_source=ReportSource.Web.value, tone=Tone.Objective)
        detailed.gpt_researcher.verbose = False
        report = await detailed.run()
        return detailed.gpt_researcher, report

    report_type = ReportType.DeepResearch.value if mode == "deep" else question.get(
        "report_type", ReportType.ResearchReport.value)
    researcher = GPTResearcher(query=query, report_type=report_type, report_format="markdown",
                               report_source=ReportSource.Web.value, tone=Tone.Objective,
                               verbose=False)
    await researcher.conduct_research()
    report = await researcher.write_report()
    return researcher, report


async def run_one(question: dict, mode: str, *, dataset: str | Path,
                  runs_dir: str | Path = RUNS_DIR) -> Path:
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; expected one of {MODES}")
    started = datetime.now(timezone.utc)
    run_id = f"{started:%Y%m%dT%H%M%S}_{question['question_id']}_{mode}_{uuid.uuid4().hex[:6]}"
    tracer = Tracer(trace_id=run_id)
    capture = RunCapture(tracer)
    researcher, report, error = None, "", None
    t0 = time.perf_counter()
    with capture:
        with tracer.span("run", query=question["question"], mode=mode) as root:
            try:
                researcher, report = await _research(question, mode)
            except Exception as e:  # recorded, not raised: a failed run is still data
                error = f"{type(e).__name__}: {e}"
                root.status, root.error = "error", error
    meta = {
        "run_id": run_id,
        "trace_id": tracer.trace_id,
        "question_id": question["question_id"],
        "query": question["question"],
        "dataset_version": dataset_version(dataset),
        "agent_commit": agent_commit(),
        "started_at": started.isoformat(),
        "duration_s": round(time.perf_counter() - t0, 2),
        "cost_usd": round(capture.cost_usd, 6),
        "status": "error" if error else "ok",
        "error": error,
        "config": run_config(researcher, mode, capture) if researcher else {"mode": mode},
        "health": {**capture.health, "context_parse_warnings": len(capture.parse_warnings)},
    }
    archive = build_archive(meta=meta, spans=tracer.to_list(), chunks=capture.chunks,
                            report_markdown=report)
    return save_archive(archive, Path(runs_dir) / dataset_version(dataset) / f"{run_id}.json")


async def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default=str(DATASET))
    ap.add_argument("--modes", default=",".join(MODES),
                    help="comma-separated subset of default,detailed,deep")
    ap.add_argument("--questions", default="", help="comma-separated question_ids (default: all)")
    ap.add_argument("--limit", type=int, default=0, help="run only the first N questions")
    ap.add_argument("--runs-dir", default=str(RUNS_DIR))
    args = ap.parse_args(argv)

    from dotenv import load_dotenv
    load_dotenv()

    questions = load_questions(args.dataset)
    if args.questions:
        wanted = set(args.questions.split(","))
        questions = [q for q in questions if q["question_id"] in wanted]
    if args.limit:
        questions = questions[:args.limit]
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]

    failed = 0
    for q in questions:
        for mode in modes:
            if mode not in q.get("modes", MODES):
                continue
            print(f">> {q['question_id']} [{mode}] {q['question']}")
            path = await run_one(q, mode, dataset=args.dataset, runs_dir=args.runs_dir)
            status = json.loads(path.read_text(encoding="utf-8"))["meta"]["status"]
            failed += status != "ok"
            print(f"   {status}: {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
