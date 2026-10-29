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
from .metrics.base import Metric, MetricResult, ScoringContext

SCORER_BASE_VERSION = "0.1"
RESULTS_DIR = Path(__file__).parent / "results"


def scorer_version(metrics: list[Metric]) -> str:
    fingerprint = stable_hash(sorted(
        (m.name, m.version, [(p.id, p.version, p.hash) for p in m.prompts]) for m in metrics))
    return f"{SCORER_BASE_VERSION}+{fingerprint[:8]}"


async def score_archive(archive: RunArchive, metrics: list[Metric],
                        ctx: ScoringContext) -> dict:
    results: dict[str, dict] = {}
    for m in metrics:
        try:
            r = await m.score(archive, ctx)
        except Exception as e:
            r = MetricResult(m.name, m.category, m.version, None, m.higher_is_better,
                             {"traceback": traceback.format_exc(limit=5)},
                             skipped=f"error: {type(e).__name__}: {e}")
        results[m.name] = r.to_dict()
    return {
        "run_id": archive.run_id,
        "question_id": archive.question_id,
        "mode": archive.meta.get("config", {}).get("mode"),
        "scorer_version": scorer_version(metrics),
        "scored_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "judge_model": ctx.judge.model if ctx.judge else None,
        "embedding_model": ctx.embedder.model if ctx.embedder else None,
        "metrics": results,
    }


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
