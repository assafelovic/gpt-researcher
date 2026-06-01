"""
Eval Log Comparator
-------------------
Compare two quality_eval JSONL log files and print a diff table showing
metric changes between runs (e.g. before/after a code change).

Usage:
    python -m evals.quality_eval.compare logs/run_a.jsonl logs/run_b.jsonl
    python -m evals.quality_eval.compare logs/run_a.jsonl logs/run_b.jsonl --detail
"""

import argparse
import json
from pathlib import Path


# Metrics to compare and their display labels
METRICS = [
    ("aggregate_metrics.avg_citation_ratio",         "citation_ratio"),
    ("aggregate_metrics.avg_diversity_ratio",        "diversity_ratio"),
    ("aggregate_metrics.avg_domain_entropy",         "domain_entropy"),
    ("aggregate_metrics.avg_authority_score",        "authority_score"),
    ("aggregate_metrics.avg_subtopic_coverage_rate", "subtopic_coverage"),
    ("aggregate_metrics.hallucination_rate",         "hallucination_rate"),
    ("aggregate_metrics.avg_claim_score",            "avg_claim_score"),
    ("aggregate_metrics.avg_unsupported_claim_rate", "unsupported_claim_rate"),
    ("aggregate_metrics.avg_inferred_claim_rate",    "inferred_claim_rate"),
    ("aggregate_metrics.avg_latency_seconds",        "latency_avg (s)"),
    ("aggregate_metrics.avg_cost",                   "cost_avg ($)"),
    ("aggregate_metrics.successful",                 "successful"),
    ("aggregate_metrics.failed",                     "failed"),
]


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.loads(f.readline().strip())


def _get(obj: dict, dotpath: str):
    """Traverse a dot-separated key path."""
    parts = dotpath.split(".")
    cur = obj
    for p in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def _fmt(val) -> str:
    if val is None:
        return "—"
    if isinstance(val, float):
        return f"{val:.3f}"
    return str(val)


def _arrow(a, b) -> str:
    """Return a direction arrow and magnitude for numeric changes."""
    if a is None or b is None:
        return ""
    try:
        diff = float(b) - float(a)
        if abs(diff) < 1e-6:
            return "  ="
        sign = "++" if diff > 0 else "--"
        return f"  {sign} {abs(diff):.3f}"
    except (TypeError, ValueError):
        return ""


def compare(path_a: str, path_b: str, detail: bool = False):
    log_a = _load(path_a)
    log_b = _load(path_b)

    meta_a = log_a.get("run_metadata", {})
    meta_b = log_b.get("run_metadata", {})

    # Header
    name_a = Path(path_a).name
    name_b = Path(path_b).name
    print(f"\n{'='*70}")
    print(f"  EVAL COMPARISON")
    print(f"{'='*70}")
    print(f"  A: {name_a}")
    print(f"     commit={meta_a.get('git_commit','?')}  "
          f"model={meta_a.get('researcher_model','?')}  "
          f"n={meta_a.get('num_examples','?')}  "
          f"ts={meta_a.get('timestamp','?')[:19]}")
    print(f"  B: {name_b}")
    print(f"     commit={meta_b.get('git_commit','?')}  "
          f"model={meta_b.get('researcher_model','?')}  "
          f"n={meta_b.get('num_examples','?')}  "
          f"ts={meta_b.get('timestamp','?')[:19]}")
    print(f"{'='*70}")
    print(f"  {'Metric':<28} {'A':>10} {'B':>10}  {'Change'}")
    print(f"  {'-'*28} {'-'*10} {'-'*10}  {'-'*12}")

    for dotpath, label in METRICS:
        val_a = _get(log_a, dotpath)
        val_b = _get(log_b, dotpath)
        if val_a is None and val_b is None:
            continue
        arrow = _arrow(val_a, val_b)
        print(f"  {label:<28} {_fmt(val_a):>10} {_fmt(val_b):>10}{arrow}")

    print(f"{'='*70}\n")

    if detail:
        _detail_diff(log_a, log_b, name_a, name_b)


def _detail_diff(log_a: dict, log_b: dict, label_a: str, label_b: str):
    """Per-query diff for queries that appear in both logs."""
    results_a = {r["query"]: r for r in log_a.get("results", []) if "query" in r}
    results_b = {r["query"]: r for r in log_b.get("results", []) if "query" in r}

    shared = set(results_a) & set(results_b)
    if not shared:
        print("  No matching queries found between the two runs.\n")
        return

    print(f"  PER-QUERY DETAIL ({len(shared)} shared queries)")
    print(f"  {'Query':<45} {'citation':>8} {'authority':>10} {'claim_score':>12}")
    print(f"  {'-'*45} {'-'*8} {'-'*10} {'-'*12}")

    for q in sorted(shared):
        ra = results_a[q]
        rb = results_b[q]

        def _diff_field(obj_a, obj_b, *keys):
            va = obj_a
            vb = obj_b
            for k in keys:
                va = va.get(k) if isinstance(va, dict) else None
                vb = vb.get(k) if isinstance(vb, dict) else None
            if va is None and vb is None:
                return "      —"
            fa, fb = _fmt(va), _fmt(vb)
            arrow = _arrow(va, vb)
            return f"{fa}→{fb}{arrow}"

        cit  = _diff_field(ra, rb, "citation_coverage",  "citation_ratio")
        auth = _diff_field(ra, rb, "source_authority",   "avg_authority_score")
        clm  = _diff_field(ra, rb, "unsupported_claim",  "avg_claim_score")

        truncated = (q[:42] + "...") if len(q) > 45 else q
        print(f"  {truncated:<45} {cit:>8} {auth:>10} {clm:>12}")

    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare two quality_eval log files")
    parser.add_argument("log_a", help="Path to first log file (baseline)")
    parser.add_argument("log_b", help="Path to second log file (new run)")
    parser.add_argument("--detail", action="store_true",
                        help="Show per-query breakdown for shared queries")
    args = parser.parse_args()

    compare(args.log_a, args.log_b, detail=args.detail)
