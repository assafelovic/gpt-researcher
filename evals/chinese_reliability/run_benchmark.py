"""Run the fixed Chinese reliability benchmark serially."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from .metrics import build_run_metrics, summarize_runs
from .source_validator import SourceValidator


HERE = Path(__file__).resolve().parent
DEFAULT_QUERIES_PATH = HERE / "queries.json"
DEFAULT_OUTPUT_ROOT = Path("outputs") / "evals" / "chinese_reliability"
SAFE_ENV_KEYS = (
    "FAST_LLM",
    "SMART_LLM",
    "STRATEGIC_LLM",
    "RETRIEVER",
    "SCRAPER",
    "EMBEDDING",
    "REPORT_SOURCE",
    "LANGUAGE",
    "MAX_SEARCH_RESULTS_PER_QUERY",
)


def load_cases(
    path: str | Path,
    limit: int | None = None,
    ids: list[str] | None = None,
) -> list[dict]:
    cases = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError("queries file must contain a JSON list")

    seen_ids: set[str] = set()
    for case in cases:
        required = {"id", "question", "report_type"}
        if not isinstance(case, dict) or not required.issubset(case):
            raise ValueError("each query must contain id, question and report_type")
        if case["id"] in seen_ids:
            raise ValueError(f"duplicate query id: {case['id']}")
        if case["report_type"] not in {"research_report", "deep"}:
            raise ValueError(f"unsupported report type: {case['report_type']}")
        seen_ids.add(case["id"])

    if ids:
        if limit is not None:
            raise ValueError("limit and ids cannot be used together")
        cases_by_id = {case["id"]: case for case in cases}
        missing = [case_id for case_id in ids if case_id not in cases_by_id]
        if missing:
            raise ValueError(f"unknown query ids: {', '.join(missing)}")
        return [cases_by_id[case_id] for case_id in ids]
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        return cases[:limit]
    return cases


def default_researcher_factory(**kwargs):
    # Delayed import keeps metric/unit tests independent of the full app stack.
    from gpt_researcher.agent import GPTResearcher

    return GPTResearcher(**kwargs)


async def run_single_case(
    case: dict,
    *,
    researcher_factory: Callable = default_researcher_factory,
    validator: SourceValidator | None = None,
) -> dict:
    validator = validator or SourceValidator()
    report = ""
    source_results = []
    error = None
    cost = None
    started = time.perf_counter()

    try:
        researcher = researcher_factory(
            query=case["question"],
            report_type=case["report_type"],
            report_format="markdown",
            language="Chinese (Simplified)",
            verbose=False,
        )
        await researcher.conduct_research()
        report = await researcher.write_report()
        source_results = await validator.validate_many(researcher.get_source_urls())
        cost = researcher.get_costs()
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"

    duration_seconds = time.perf_counter() - started
    is_deep = case["report_type"] == "deep"
    metrics = build_run_metrics(
        report=report,
        source_results=source_results,
        duration_seconds=duration_seconds,
        cost=cost,
        error=error,
        min_report_chars=1500 if is_deep else 400,
        min_valid_sources=5 if is_deep else 2,
    )
    return {
        "id": case["id"],
        "question": case["question"],
        "category": case.get("category", ""),
        "report_type": case["report_type"],
        "report": report,
        "source_results": [asdict(result) for result in source_results],
        "retry_count": 0,
        **metrics,
    }


def _summary_markdown(metadata: dict, summaries: dict) -> str:
    lines = [
        "# 中文报告可靠性评测结果",
        "",
        f"- 模式：`{metadata['mode']}`",
        f"- Git提交：`{metadata['git_commit']}`",
        f"- 运行时间：`{metadata['timestamp']}`",
        "",
        "| 报告模式 | 题目数 | 成功率 | 有效引用率 | 平均耗时（秒） | 平均成本 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    labels = {"overall": "整体", "research_report": "Simple", "deep": "Deep"}
    for key in ("overall", "research_report", "deep"):
        summary = summaries[key]
        duration = summary["average_duration_seconds"]
        cost = summary["average_cost"]
        lines.append(
            "| {label} | {count} | {success:.1%} | {valid:.1%} | {duration} | {cost} |".format(
                label=labels[key],
                count=summary["total_queries"],
                success=summary["report_success_rate"],
                valid=summary["valid_citation_rate"],
                duration=f"{duration:.1f}" if duration is not None else "-",
                cost=f"${cost:.4f}" if cost is not None else "-",
            )
        )
    return "\n".join(lines) + "\n"


def build_output_documents(runs: Iterable[dict], metadata: dict) -> dict[Path, str]:
    """Build all benchmark output files without performing filesystem I/O."""
    run_list = list(runs)
    documents: dict[Path, str] = {}
    for run in run_list:
        documents[Path("reports") / f"{run['id']}.md"] = run.get("report", "")

    records = []
    for run in run_list:
        record = {key: value for key, value in run.items() if key != "report"}
        records.append(json.dumps(record, ensure_ascii=False))
    documents[Path("runs.jsonl")] = "\n".join(records) + ("\n" if records else "")

    simple_runs = [run for run in run_list if run["report_type"] == "research_report"]
    deep_runs = [run for run in run_list if run["report_type"] == "deep"]
    summaries = {
        "overall": summarize_runs(run_list),
        "research_report": summarize_runs(simple_runs),
        "deep": summarize_runs(deep_runs),
    }
    payload = {"metadata": metadata, "summaries": summaries}
    documents[Path("summary.json")] = json.dumps(
        payload, ensure_ascii=False, indent=2
    )
    documents[Path("summary-simple.json")] = json.dumps(
        summaries["research_report"], ensure_ascii=False, indent=2
    )
    documents[Path("summary-deep.json")] = json.dumps(
        summaries["deep"], ensure_ascii=False, indent=2
    )
    documents[Path("summary.md")] = _summary_markdown(metadata, summaries)
    return documents


def write_outputs(output_dir: str | Path, runs: Iterable[dict], metadata: dict) -> None:
    output_path = Path(output_dir)
    for relative_path, content in build_output_documents(runs, metadata).items():
        destination = output_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


def get_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def build_metadata(mode: str) -> dict:
    return {
        "mode": mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "configuration": {key: os.getenv(key, "") for key in SAFE_ENV_KEYS},
    }


async def run_benchmark(cases: list[dict], output_dir: Path, metadata: dict) -> list[dict]:
    runs: list[dict] = []
    validator = SourceValidator()
    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['id']} {case['question']}", flush=True)
        result = await run_single_case(case, validator=validator)
        runs.append(result)
        write_outputs(output_dir, runs, metadata)
        state = "成功" if result["report_success"] else "未达成功标准"
        print(
            f"  {state}; 有效引用 {result['valid_citation_count']}/"
            f"{result['citation_count']}; 耗时 {result['duration_seconds']:.1f}s",
            flush=True,
        )
    return runs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Chinese report reliability benchmark")
    parser.add_argument("--mode", choices=("baseline", "enhanced"), default="baseline")
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES_PATH)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--ids", nargs="+")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    output_dir = args.output_dir or DEFAULT_OUTPUT_ROOT / args.mode
    cases = load_cases(args.queries, args.limit, args.ids)
    metadata = build_metadata(args.mode)
    asyncio.run(run_benchmark(cases, output_dir, metadata))
    print(f"结果已保存：{output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
