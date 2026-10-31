"""
Scoring layer: archive in, per-metric results out.
--------------------------------------------------
Results are keyed by run_id + scorer version. The scorer version combines a
hand-bumped base version with a hash of every metric's version and prompt
hashes, so any change to a metric or prompt produces a new key instead of
overwriting older results.
"""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path

from .archive import RunArchive
from .cache import stable_hash
from .citation_audit import AUDIT_VERSION
from .metrics.base import Metric, MetricResult, ScoringContext
from .report_parser import body_paragraphs

SCORER_BASE_VERSION = "0.2"      # 0.2: failed runs are skipped
RESULTS_DIR = Path(__file__).parent / "results"


def scorer_version(metrics: list[Metric]) -> str:
    fingerprint = stable_hash(sorted(
        (m.name, m.version, [(p.id, p.version, p.hash) for p in m.prompts]) for m in metrics))
    return f"{SCORER_BASE_VERSION}+{fingerprint[:8]}"


MIN_REPORT_CHARS = 1000


def run_failure(archive: RunArchive) -> str | None:
    """Why a run is not worth scoring, or None.

    A run fails when the agent raised (meta.status != "ok") or when it finished
    without a real report: no citations at all and under MIN_REPORT_CHARS of
    text, e.g. deep research's fallback sentence after every sub-query failed.
    Scoring such a run only drags the averages down with numbers about nothing.
    """
    status = archive.meta.get("status", "ok")
    if status != "ok":
        return f"run status {status}: {archive.meta.get('error') or 'no error message'}"
    parsed = archive.report
    has_citations = bool(parsed.get("references")) or any(
        p["citations"] for p in body_paragraphs(parsed))
    text = archive.report_markdown.strip()
    if not has_citations and len(text) < MIN_REPORT_CHARS:
        return f"no real report ({len(text)} chars, no citations)"
    return None


async def score_archive(archive: RunArchive, metrics: list[Metric],
                        ctx: ScoringContext, *, score_failed: bool = False) -> dict:
    results: dict[str, dict] = {}
    failure = run_failure(archive)
    for m in metrics:
        if failure and not score_failed:
            results[m.name] = MetricResult(m.name, m.category, m.version, None, m.higher_is_better,
                                           {}, skipped=f"failed run: {failure}").to_dict()
            continue
        try:
            r = await m.score(archive, ctx)
        except Exception as e:
            r = MetricResult(m.name, m.category, m.version, None, m.higher_is_better,
                             {"traceback": traceback.format_exc(limit=5)},
                             skipped=f"error: {type(e).__name__}: {e}")
        results[m.name] = r.to_dict()
    record = {
        "run_id": archive.run_id,
        "question_id": archive.question_id,
        "mode": archive.meta.get("config", {}).get("mode"),
        "scorer_version": scorer_version(metrics),
        "scored_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "judge_model": ctx.judge.model if ctx.judge else None,
        "embedding_model": ctx.embedder.model if ctx.embedder else None,
        "run_status": "failed" if failure else "ok",
        "failure": failure,
        "metrics": results,
    }
    audit = ctx.archive_memo(archive).get("citation_audit")
    if audit is not None:
        # Every claim and citing sentence with its verdict, so a person can check
        # what the audit metrics counted (they keep only flagged items).
        record["citation_audit"] = {"version": AUDIT_VERSION,
                                    "paragraphs": [p.to_dict() for p in audit.paragraphs]}
    return record


def save_results(record: dict, results_dir: str | Path = RESULTS_DIR) -> Path:
    path = Path(results_dir) / record["run_id"] / f"{record['scorer_version']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def summary_rows(record: dict) -> list[tuple[str, str, str]]:
    """(metric, value, note) rows for printing; no totals."""
    rows = []
    for name, r in record["metrics"].items():
        value = "—" if r["value"] is None else f"{r['value']:.3f}"
        note = r["skipped"] or ("lower is better" if not r["higher_is_better"] else "")
        rows.append((name, value, note))
    return rows
