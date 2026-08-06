"""Metric calculations shared by baseline and enhanced benchmark runs."""

from __future__ import annotations

from numbers import Real
from typing import Iterable, Mapping, Sequence

from .source_validator import SourceValidationResult


def build_run_metrics(
    *,
    report: str,
    source_results: Sequence[SourceValidationResult],
    duration_seconds: float,
    cost: float | None,
    error: str | None = None,
    min_report_chars: int = 800,
    min_valid_sources: int = 3,
) -> dict:
    citation_count = len(source_results)
    valid_citation_count = sum(
        result.status == "valid" for result in source_results
    )
    valid_citation_rate = (
        valid_citation_count / citation_count if citation_count else 0.0
    )
    report_success = (
        error is None
        and len(report.strip()) >= min_report_chars
        and valid_citation_count >= min_valid_sources
    )
    return {
        "duration_seconds": round(duration_seconds, 3),
        "cost": float(cost) if isinstance(cost, Real) else None,
        "report_length": len(report.strip()),
        "citation_count": citation_count,
        "valid_citation_count": valid_citation_count,
        "valid_citation_rate": valid_citation_rate,
        "report_success": report_success,
        "error": error,
    }


def summarize_runs(runs: Iterable[Mapping]) -> dict:
    run_list = list(runs)
    completed = [run for run in run_list if not run.get("error")]
    costs = [
        float(run["cost"])
        for run in completed
        if isinstance(run.get("cost"), Real)
    ]
    citation_count = sum(int(run.get("citation_count", 0)) for run in run_list)
    valid_citation_count = sum(
        int(run.get("valid_citation_count", 0)) for run in run_list
    )

    return {
        "total_queries": len(run_list),
        "completed_queries": len(completed),
        "failed_queries": len(run_list) - len(completed),
        "successful_reports": sum(bool(run.get("report_success")) for run in run_list),
        "report_success_rate": (
            sum(bool(run.get("report_success")) for run in run_list) / len(run_list)
            if run_list
            else 0.0
        ),
        "citation_count": citation_count,
        "valid_citation_count": valid_citation_count,
        "valid_citation_rate": (
            valid_citation_count / citation_count if citation_count else 0.0
        ),
        "average_duration_seconds": (
            sum(float(run["duration_seconds"]) for run in completed) / len(completed)
            if completed
            else None
        ),
        "average_cost": sum(costs) / len(costs) if costs else None,
    }
