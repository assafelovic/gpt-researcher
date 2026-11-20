"""
Confidence intervals for scoring results (bootstrap), no model calls.
---------------------------------------------------------------------
Reads the result records that score.py wrote (one folder per run, the newest
record in each) and prints, per metric and mode, the mean with a 95%
bootstrap interval. With --compare, the paired difference between two result
folders scored on the same runs; with --noise, signal to noise against a
noise round (--judge-salt) of the same runs.

The bootstrap resamples questions, not reports: the reports of one question
share their key points, rubric and material, so they are not independent.
Each resample draws as many questions as there are, with replacement, and
takes every report of the drawn questions (per mode: that question's report
in the mode). The interval is the 2.5th to 97.5th percentile of the resampled
means. With five questions an interval is wide; that is the honest width.

Usage:
    python -m evals.research_eval.stats RESULTS_DIR
    python -m evals.research_eval.stats RESULTS_DIR --compare OTHER_DIR   # OTHER - RESULTS
    python -m evals.research_eval.stats RESULTS_DIR --noise NOISE_DIR
    python -m evals.research_eval.stats RESULTS_DIR --json out.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

ALL = "all"
RESAMPLES = 10000


def load_results(results_dir: str | Path) -> dict[str, dict]:
    """run_id -> the newest result record of that run (by scored_at)."""
    out: dict[str, dict] = {}
    for run_dir in sorted(Path(results_dir).iterdir()):
        if not run_dir.is_dir():
            continue
        records = []
        for f in run_dir.glob("*.json"):
            try:
                rec = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(rec, dict) and "metrics" in rec and "run_id" in rec:
                records.append(rec)
        if records:
            newest = max(records, key=lambda r: r.get("scored_at") or "")
            out[newest["run_id"]] = newest
    return out


def values(records: dict[str, dict], metric: str, mode: str = ALL) -> dict[str, float]:
    """run_id -> value of `metric`, for runs in `mode` that have one."""
    out = {}
    for run_id, rec in records.items():
        if mode != ALL and rec.get("mode") != mode:
            continue
        r = rec["metrics"].get(metric)
        if r and r.get("value") is not None:
            out[run_id] = float(r["value"])
    return out


def percentile(sorted_xs: list[float], q: float) -> float:
    """Linear interpolation between closest ranks, q in [0, 1]."""
    if not sorted_xs:
        return math.nan
    pos = q * (len(sorted_xs) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (pos - lo)


def cluster_bootstrap(per_run: dict[str, float], question_of: dict[str, str],
                      resamples: int = RESAMPLES, seed: int = 0) -> tuple[float, float, float]:
    """(mean, low, high): mean over runs and its 95% interval, resampling questions."""
    if not per_run:
        return math.nan, math.nan, math.nan
    groups: dict[str, list[float]] = {}
    for run_id, v in per_run.items():
        groups.setdefault(question_of.get(run_id, run_id), []).append(v)
    clusters = list(groups.values())
    mean = sum(per_run.values()) / len(per_run)
    if len(clusters) < 2:
        return mean, math.nan, math.nan
    rng = random.Random(seed)
    means = []
    for _ in range(resamples):
        picked = [x for _ in clusters for x in rng.choice(clusters)]
        means.append(sum(picked) / len(picked))
    means.sort()
    return mean, percentile(means, 0.025), percentile(means, 0.975)


def metric_names(*record_sets: dict[str, dict]) -> list[str]:
    names: dict[str, None] = {}
    for records in record_sets:
        for rec in records.values():
            for n in rec["metrics"]:
                names.setdefault(n, None)
    return list(names)


def modes_of(records: dict[str, dict]) -> list[str]:
    order = ["default", "detailed", "deep"]
    found = {r.get("mode") for r in records.values() if r.get("mode")}
    return [m for m in order if m in found] + sorted(found - set(order)) + [ALL]


def summarize(records: dict[str, dict], resamples: int = RESAMPLES, seed: int = 0) -> list[dict]:
    q = {r: rec.get("question_id") or r for r, rec in records.items()}
    rows = []
    for metric in metric_names(records):
        for mode in modes_of(records):
            v = values(records, metric, mode)
            if not v:
                continue
            mean, lo, hi = cluster_bootstrap(v, q, resamples, seed)
            rows.append({"metric": metric, "mode": mode, "n": len(v), "mean": mean, "low": lo, "high": hi})
    return rows


def compare(base: dict[str, dict], other: dict[str, dict], resamples: int = RESAMPLES,
            seed: int = 0) -> list[dict]:
    """Paired difference other - base on the runs both folders scored."""
    q = {r: rec.get("question_id") or r for r, rec in {**base, **other}.items()}
    rows = []
    for metric in metric_names(base, other):
        for mode in modes_of(base):
            a, b = values(base, metric, mode), values(other, metric, mode)
            diff = {r: b[r] - a[r] for r in a.keys() & b.keys()}
            if not diff:
                continue
            mean, lo, hi = cluster_bootstrap(diff, q, resamples, seed)
            rows.append({"metric": metric, "mode": mode, "n": len(diff), "diff": mean, "low": lo, "high": hi,
                         "differs": not (math.isnan(lo) or lo <= 0 <= hi)})
    return rows


def _sd(xs: list[float]) -> float:
    if len(xs) < 2:
        return math.nan
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def signal_to_noise(main: dict[str, dict], noise: dict[str, dict]) -> list[dict]:
    """Per metric over all runs both rounds scored: spread across reports
    divided by the judge's own spread (sd of main - noise, / sqrt 2 for one
    scoring), and the smallest difference in a mean over these runs that
    exceeds the noise (2 * noise sd / sqrt n)."""
    rows = []
    for metric in metric_names(main):
        a, b = values(main, metric), values(noise, metric)
        common = sorted(a.keys() & b.keys())
        if len(common) < 3:
            continue
        noise_sd = _sd([a[r] - b[r] for r in common]) / math.sqrt(2)
        signal = _sd([a[r] for r in common])
        rows.append({"metric": metric, "n": len(common), "signal_sd": signal, "noise_sd": noise_sd,
                     "snr": signal / noise_sd if noise_sd else math.inf,
                     "mdd": 2 * noise_sd / math.sqrt(len(common))})
    return rows


def _f(x: float) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-"
    if isinstance(x, float) and math.isinf(x):
        return "inf"
    return f"{x:.3f}"


def render(summary: list[dict], diffs: list[dict] | None, snr: list[dict] | None) -> str:
    lines = ["## Means with 95% intervals (bootstrap over questions)", "",
             "| metric | mode | n | mean | 95% interval |", "|---|---|---|---|---|"]
    lines += [f"| {r['metric']} | {r['mode']} | {r['n']} | {_f(r['mean'])} | {_f(r['low'])} – {_f(r['high'])} |"
              for r in summary]
    if diffs is not None:
        lines += ["", "## Paired difference (other − base)", "",
                  "| metric | mode | n | diff | 95% interval | differs |", "|---|---|---|---|---|---|"]
        lines += [f"| {r['metric']} | {r['mode']} | {r['n']} | {_f(r['diff'])} | {_f(r['low'])} – {_f(r['high'])} | "
                  f"{'yes' if r['differs'] else ''} |" for r in diffs]
    if snr is not None:
        lines += ["", "## Signal to noise (all runs)", "",
                  "| metric | n | signal sd | noise sd | SNR | min. detectable diff |", "|---|---|---|---|---|---|"]
        lines += [f"| {r['metric']} | {r['n']} | {_f(r['signal_sd'])} | {_f(r['noise_sd'])} | {_f(r['snr'])} | "
                  f"{_f(r['mdd'])} |" for r in snr]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results_dir")
    ap.add_argument("--compare", help="a second results folder; prints other - base per run, paired")
    ap.add_argument("--noise", help="a noise-round results folder of the same runs")
    ap.add_argument("--resamples", type=int, default=RESAMPLES)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json", help="also write all rows to this file")
    args = ap.parse_args(argv)
    base = load_results(args.results_dir)
    if not base:
        ap.error(f"no result records in {args.results_dir}")
    summary = summarize(base, args.resamples, args.seed)
    diffs = compare(base, load_results(args.compare), args.resamples, args.seed) if args.compare else None
    snr = signal_to_noise(base, load_results(args.noise)) if args.noise else None
    print(render(summary, diffs, snr), end="")
    if args.json:
        Path(args.json).write_text(json.dumps({"summary": summary, "compare": diffs, "snr": snr},
                                              indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
