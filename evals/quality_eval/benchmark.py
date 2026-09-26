"""
Benchmark Runner
----------------
Compares 4 GPT-Researcher configurations across 8 research topics using
the quality_eval metric suite.

Configurations:
  single-gpt4o       — GPTResearcher    + gpt-4o
  single-gpt4o-mini  — GPTResearcher    + gpt-4o-mini
  multi-gpt4o        — ChiefEditorAgent + gpt-4o
  multi-gpt4o-mini   — ChiefEditorAgent + gpt-4o-mini

Topics span high-authority domains (medical, legal, science) and
low-authority domains (AI/tech, finance) to validate metric discrimination.

Usage:
    python -m evals.quality_eval.benchmark
    python -m evals.quality_eval.benchmark --configs single-gpt4o multi-gpt4o
    python -m evals.quality_eval.benchmark --no-llm-metrics
    python -m evals.quality_eval.benchmark --summary-only
    python -m evals.quality_eval.benchmark --compare LOG_A LOG_B [--detail]
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from evals.quality_eval.metrics import evaluate_report, is_skipped as _is_skipped

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

QUERIES = {
    "medical":   "Current treatments and clinical outcomes for Type 2 diabetes",
    "legal":     "Legal implications of AI-generated content and copyright law",
    "history":   "Causes of the fall of the Western Roman Empire",
    "climate":   "Latest scientific findings on climate change and sea level rise",
    "ai_tech":   "Latest developments in large language models in 2024",
    "finance":   "How does the Federal Reserve control inflation through monetary policy",
    "physics":   "Principles of quantum entanglement and quantum computing",
    "chemistry": "Mechanism of nucleophilic substitution reactions in organic chemistry",
}

CONFIGS = [
    {"name": "single-gpt4o",      "arch": "single", "model": "gpt-4o"},
    {"name": "single-gpt4o-mini", "arch": "single", "model": "gpt-4o-mini"},
    {"name": "multi-gpt4o",       "arch": "multi",  "model": "gpt-4o"},
    {"name": "multi-gpt4o-mini",  "arch": "multi",  "model": "gpt-4o-mini"},
]

GRADER_MODEL_NAME = "gpt-4-turbo"
LOGS_DIR = Path(__file__).parent / "logs"

# High-authority topics — tagged HIGH in the per-topic summary (others shown "low").
HIGH_AUTHORITY_TOPICS = {"medical", "legal", "physics", "chemistry", "climate", "history"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Researcher runners
# ---------------------------------------------------------------------------

def _set_token_limit(model: str):
    """gpt-4-turbo caps completion at 4096; default SMART_TOKEN_LIMIT (6000) errors."""
    os.environ["SMART_TOKEN_LIMIT"] = "4000" if model == "gpt-4-turbo" else "6000"


async def _run_single_agent(query: str, model: str):
    """Run GPTResearcher and return (report, sources, context)."""
    os.environ["SMART_LLM"] = f"openai:{model}"
    _set_token_limit(model)

    from gpt_researcher.agent import GPTResearcher
    from gpt_researcher.utils.enum import ReportType, ReportSource, Tone

    researcher = GPTResearcher(
        query=query,
        report_type=ReportType.ResearchReport.value,
        report_format="markdown",
        report_source=ReportSource.Web.value,
        tone=Tone.Objective,
        verbose=False,
    )
    context = await researcher.conduct_research()
    report  = await researcher.write_report()
    sources = researcher.get_source_urls()
    cost    = researcher.get_costs()
    return report, sources, context, cost


async def _run_multi_agent(query: str, model: str):
    """Run ChiefEditorAgent and return (report, sources, context).

    The multi-agent workflow only surfaces LLM-formatted markdown citations
    in its final state (already filtered to "used" sources), which makes
    citation/diversity incomparable to the single-agent path. To recover the
    raw visited URLs — the same denominator the single-agent uses — we hook
    GPTResearcher.conduct_research and collect every sub-researcher's
    visited_urls and context. This patches only the test process, not the
    upstream library.
    """
    os.environ["SMART_LLM"]     = f"openai:{model}"
    os.environ["STRATEGIC_LLM"] = f"openai:{model}"
    _set_token_limit(model)

    from multi_agents.agents.orchestrator import ChiefEditorAgent
    from gpt_researcher import GPTResearcher

    collected_urls: list[str] = []
    collected_ctx:  list[str] = []
    _orig = GPTResearcher.conduct_research

    async def _patched(self, *a, **k):
        res = await _orig(self, *a, **k)
        try:
            collected_urls.extend(self.visited_urls)
            collected_ctx.append(str(res))
        except Exception:
            pass
        return res

    task = {
        "query":                query,
        "model":                model,
        "max_sections":         3,
        "max_plan_revisions":   1,
        "include_human_feedback": False,
        "follow_guidelines":    False,
        "publish_formats":      {"markdown": True},
        "verbose":              False,
    }

    GPTResearcher.conduct_research = _patched
    try:
        chief  = ChiefEditorAgent(task)
        result = await chief.run_research_task(task_id=uuid.uuid4())
    finally:
        GPTResearcher.conduct_research = _orig

    report  = result.get("report", "")
    sources = list(dict.fromkeys(collected_urls))          # dedup, preserve order
    context = "\n\n".join(collected_ctx) or result.get("initial_research", "")
    return report, sources, context, None   # multi-agent cost not easily tracked


# ---------------------------------------------------------------------------
# Per-query evaluation
# ---------------------------------------------------------------------------

async def _evaluate_query(
    topic: str,
    query: str,
    config: dict,
    grader_model,
    run_llm_metrics: bool,
) -> dict:
    arch  = config["arch"]
    model = config["model"]

    print(f"\n   [{topic}] {query[:60]}...")
    t0 = time.perf_counter()

    try:
        if arch == "single":
            report, sources, context, cost = await _run_single_agent(query, model)
        else:
            report, sources, context, cost = await _run_multi_agent(query, model)
    except Exception as e:
        print(f"      [ERROR] researcher failed: {e}")
        return {"topic": topic, "query": query, "error": str(e)}

    latency = round(time.perf_counter() - t0, 2)
    print(f"      report={len(report)} chars  sources={len(sources)}  latency={latency}s")

    m = await evaluate_report(
        report, sources, context, query, grader_model,
        run_subtopic=run_llm_metrics, run_unsupported=run_llm_metrics,
    )
    citation    = m["citation_faithfulness"]
    diversity   = m["source_diversity"]
    authority   = m["source_authority"]
    subtopic    = m["subtopic_coverage"]
    unsupported = m["unsupported_claim"]

    # --- Console summary ---
    def _p(label, v, fn):
        if _is_skipped(v):
            print(f"      {label:<22} SKIPPED")
        else:
            fn(v)

    _p("citation:", citation,
       lambda v: print(f"      citation_faithful:     "
                       + (f"{v['citation_faithfulness']:.2f}"
                          if v.get('citation_faithfulness') is not None else 'n/a')))
    _p("diversity_ratio:", diversity,
       lambda v: print(f"      diversity_ratio:       {v['diversity_ratio']:.2f}  "
                       f"entropy={v['domain_entropy']:.2f}"))
    _p("authority_score:", authority,
       lambda v: print(f"      authority_score:       {v['avg_authority_score']:.2f}"))
    if subtopic is not None:
        _p("subtopic_coverage:", subtopic,
           lambda v: print(f"      subtopic_coverage:     "
                           f"{v.get('subtopic_coverage_rate', 'ERR'):.2f}" if v.get('subtopic_coverage_rate') is not None
                           else "      subtopic_coverage:     ERROR"))
    if unsupported is not None:
        _p("avg_claim_score:", unsupported,
           lambda v: print(f"      avg_claim_score:       {v.get('avg_claim_score', 0):.2f}  "
                           f"unsupported={v.get('unsupported_claim_rate', 0):.2f}"))

    return {
        "topic":             topic,
        "query":             query,
        "latency_seconds":   latency,
        "cost":              cost,
        "source_count":      len(sources),
        "report_length":     len(report),
        "citation_faithfulness": citation,
        "source_diversity":  diversity,
        "source_authority":  authority,
        "subtopic_coverage": subtopic,
        "unsupported_claim": unsupported,
    }


# ---------------------------------------------------------------------------
# Per-config run
# ---------------------------------------------------------------------------

def _avg(results, *key_path):
    vals = []
    for r in results:
        obj = r
        for k in key_path:
            obj = obj.get(k) if isinstance(obj, dict) else None
        if obj is not None and not _is_skipped(obj):
            vals.append(float(obj))
    return round(sum(vals) / len(vals), 3) if vals else None


async def run_config(config: dict, grader_model, run_llm_metrics: bool, max_topics: int | None = None) -> dict:
    name = config["name"]
    print(f"\n{'='*60}")
    print(f"  CONFIG: {name}  (arch={config['arch']}  model={config['model']})")
    print(f"{'='*60}")

    run_ts    = datetime.now(timezone.utc).isoformat()
    t_start   = time.perf_counter()
    results   = []

    queries = list(QUERIES.items())
    if max_topics:
        queries = queries[:max_topics]

    for topic, query in queries:
        try:
            r = await _evaluate_query(topic, query, config, grader_model, run_llm_metrics)
        except Exception as e:
            print(f"      [ERROR] unexpected: {e}")
            r = {"topic": topic, "query": query, "error": str(e)}
        results.append(r)

    successful = [r for r in results if "error" not in r]

    aggregate = {
        "avg_citation_faithfulness":  _avg(successful, "citation_faithfulness", "citation_faithfulness"),
        "avg_diversity_ratio":        _avg(successful, "source_diversity",   "diversity_ratio"),
        "avg_domain_entropy":         _avg(successful, "source_diversity",   "domain_entropy"),
        "avg_authority_score":        _avg(successful, "source_authority",   "avg_authority_score"),
        "avg_subtopic_coverage_rate": _avg(successful, "subtopic_coverage",  "subtopic_coverage_rate"),
        "avg_claim_score":            _avg(successful, "unsupported_claim",  "avg_claim_score"),
        "avg_unsupported_claim_rate": _avg(successful, "unsupported_claim",  "unsupported_claim_rate"),
        "avg_latency_seconds":        _avg(successful, "latency_seconds"),
        "successful":                 len(successful),
        "failed":                     len(results) - len(successful),
    }

    # Per-topic authority breakdown (key finding: high vs low authority domains)
    per_topic_authority = {}
    for r in successful:
        auth = r.get("source_authority")
        if auth and not _is_skipped(auth):
            per_topic_authority[r["topic"]] = auth["avg_authority_score"]

    log = {
        "run_metadata": {
            "timestamp":          run_ts,
            "git_commit":         _get_git_commit(),
            "config_name":        name,
            "arch":               config["arch"],
            "researcher_model":   config["model"],
            "grader_model":       GRADER_MODEL_NAME,
            "llm_metrics_enabled": run_llm_metrics,
            "num_topics":         len(QUERIES),
            "total_duration_seconds": round(time.perf_counter() - t_start, 2),
        },
        "aggregate_metrics":   aggregate,
        "per_topic_authority": per_topic_authority,
        "results":             results,
    }

    LOGS_DIR.mkdir(exist_ok=True)
    ts       = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = LOGS_DIR / f"benchmark_{name}_{ts}.jsonl"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(log) + "\n")
    print(f"\n  Log saved: {log_path}")

    return log


# ---------------------------------------------------------------------------
# Summary & comparison
# ---------------------------------------------------------------------------

def _dotget(obj, dotpath):
    """Traverse a dot-separated key path; None if any step is missing."""
    cur = obj
    for k in dotpath.split("."):
        cur = cur.get(k) if isinstance(cur, dict) else None
    return cur


def _fmt_val(v) -> str:
    if v is None:            return "—"
    if isinstance(v, float): return f"{v:.3f}"
    return str(v)


def _arrow(a, b) -> str:
    """Direction + magnitude for a numeric change (used by --compare)."""
    if a is None or b is None:
        return ""
    try:
        diff = float(b) - float(a)
        if abs(diff) < 1e-6:
            return "  ="
        return f"  {'++' if diff > 0 else '--'} {abs(diff):.3f}"
    except (TypeError, ValueError):
        return ""


def _print_summary(logs: list[dict]):
    """Print metrics for N configs side by side (after a run / --summary-only)."""
    if not logs:
        return

    metrics_to_show = [
        ("aggregate_metrics.avg_citation_faithfulness",  "citation_faith"),
        ("aggregate_metrics.avg_diversity_ratio",        "diversity_ratio"),
        ("aggregate_metrics.avg_authority_score",        "authority_score"),
        ("aggregate_metrics.avg_subtopic_coverage_rate", "subtopic_coverage"),
        ("aggregate_metrics.avg_claim_score",            "claim_score"),
        ("aggregate_metrics.avg_unsupported_claim_rate", "unsupported_rate"),
        ("aggregate_metrics.avg_latency_seconds",        "latency_avg (s)"),
    ]

    names = [log["run_metadata"]["config_name"] for log in logs]
    col_w = 14

    print(f"\n{'='*70}")
    print("  BENCHMARK SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Metric':<26}" + "".join(f"{n:>{col_w}}" for n in names))
    print(f"  {'-'*26}" + ("-" * col_w) * len(names))

    for dotpath, label in metrics_to_show:
        vals = [_dotget(log, dotpath) for log in logs]
        if all(v is None for v in vals):
            continue
        print(f"  {label:<26}" + "".join(f"{_fmt_val(v):>{col_w}}" for v in vals))

    # Per-topic authority breakdown
    print("\n  — Authority by Topic —")
    all_topics = set()
    for log in logs:
        all_topics.update(log.get("per_topic_authority", {}).keys())
    for topic in sorted(all_topics):
        tier = "HIGH" if topic in HIGH_AUTHORITY_TOPICS else "low "
        vals = [log.get("per_topic_authority", {}).get(topic) for log in logs]
        print(f"  [{tier}] {topic:<18}" + "".join(f"{_fmt_val(v):>{col_w}}" for v in vals))

    print(f"{'='*70}\n")


# Metrics shown in the two-run --compare diff (broader than the live summary;
# also tolerates run_eval logs, where missing fields are simply skipped).
_COMPARE_METRICS = [
    ("aggregate_metrics.avg_citation_faithfulness",  "citation_faithful"),
    ("aggregate_metrics.avg_diversity_ratio",        "diversity_ratio"),
    ("aggregate_metrics.avg_authority_score",        "authority_score"),
    ("aggregate_metrics.avg_subtopic_coverage_rate", "subtopic_coverage"),
    ("aggregate_metrics.avg_claim_score",            "avg_claim_score"),
    ("aggregate_metrics.avg_unsupported_claim_rate", "unsupported_claim_rate"),
    ("aggregate_metrics.avg_latency_seconds",        "latency_avg (s)"),
    ("aggregate_metrics.successful",                 "successful"),
    ("aggregate_metrics.failed",                     "failed"),
]


def compare_logs(path_a: str, path_b: str, detail: bool = False):
    """Diff two log files (before/after a change). One JSON object per file."""
    with open(path_a, encoding="utf-8") as f:
        log_a = json.loads(f.readline())
    with open(path_b, encoding="utf-8") as f:
        log_b = json.loads(f.readline())

    print(f"\n{'='*70}\n  EVAL COMPARISON\n{'='*70}")
    for tag, path, meta in [("A", path_a, log_a.get("run_metadata", {})),
                            ("B", path_b, log_b.get("run_metadata", {}))]:
        print(f"  {tag}: {Path(path).name}")
        print(f"     commit={meta.get('git_commit','?')}  "
              f"model={meta.get('researcher_model','?')}  ts={meta.get('timestamp','?')[:19]}")
    print(f"{'='*70}")
    print(f"  {'Metric':<28} {'A':>10} {'B':>10}  Change")
    print(f"  {'-'*28} {'-'*10} {'-'*10}  {'-'*12}")
    for dotpath, label in _COMPARE_METRICS:
        va, vb = _dotget(log_a, dotpath), _dotget(log_b, dotpath)
        if va is None and vb is None:
            continue
        print(f"  {label:<28} {_fmt_val(va):>10} {_fmt_val(vb):>10}{_arrow(va, vb)}")
    print(f"{'='*70}\n")

    if detail:
        _detail_diff(log_a, log_b)


def _detail_diff(log_a: dict, log_b: dict):
    """Per-query diff for queries present in both runs."""
    ra = {r["query"]: r for r in log_a.get("results", []) if "query" in r}
    rb = {r["query"]: r for r in log_b.get("results", []) if "query" in r}
    shared = set(ra) & set(rb)
    if not shared:
        print("  No matching queries between the two runs.\n")
        return
    print(f"  PER-QUERY DETAIL ({len(shared)} shared)")
    print(f"  {'Query':<45} {'citation':>9} {'authority':>10} {'claim':>9}")
    print(f"  {'-'*45} {'-'*9} {'-'*10} {'-'*9}")
    for q in sorted(shared):
        def _d(*keys):
            va, vb = ra[q], rb[q]
            for k in keys:
                va = va.get(k) if isinstance(va, dict) else None
                vb = vb.get(k) if isinstance(vb, dict) else None
            return f"{_fmt_val(va)}→{_fmt_val(vb)}" if (va is not None or vb is not None) else "—"
        truncated = (q[:42] + "...") if len(q) > 45 else q
        print(f"  {truncated:<45} {_d('citation_faithfulness','citation_faithfulness'):>9} "
              f"{_d('source_authority','avg_authority_score'):>10} "
              f"{_d('unsupported_claim','avg_claim_score'):>9}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _find_latest_log(config_name: str) -> Path | None:
    """Return the most recent benchmark log for a config name, or None."""
    logs = sorted(LOGS_DIR.glob(f"benchmark_{config_name}_*.jsonl"), reverse=True)
    return logs[0] if logs else None


async def main(
    config_names: list[str],
    run_llm_metrics: bool,
    resume: bool,
    summary_only: bool,
    max_topics: int | None = None,
):
    load_dotenv()
    openai_key  = os.getenv("OPENAI_API_KEY")
    tavily_key  = os.getenv("TAVILY_API_KEY")

    if not openai_key:
        raise ValueError("OPENAI_API_KEY not set")
    if not tavily_key:
        raise ValueError("TAVILY_API_KEY not set")

    os.environ["OPENAI_API_KEY"]  = openai_key
    os.environ["TAVILY_API_KEY"]  = tavily_key
    os.environ["RETRIEVER"]       = "tavily"

    grader_model = ChatOpenAI(
        temperature=0,
        model_name=GRADER_MODEL_NAME,
        openai_api_key=openai_key,
    )

    selected = [c for c in CONFIGS if c["name"] in config_names]

    if summary_only:
        logs = []
        for config in selected:
            path = _find_latest_log(config["name"])
            if path:
                with open(path, encoding="utf-8") as f:
                    logs.append(json.loads(f.readline()))
            else:
                print(f"  No log found for {config['name']}")
        _print_summary(logs)
        return

    logs = []
    for config in selected:
        if resume:
            existing = _find_latest_log(config["name"])
            if existing:
                print(f"\n  [RESUME] {config['name']} — using existing log: {existing.name}")
                with open(existing, encoding="utf-8") as f:
                    logs.append(json.loads(f.readline()))
                continue

        log = await run_config(config, grader_model, run_llm_metrics, max_topics=max_topics)
        logs.append(log)

    _print_summary(logs)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Benchmark 4 GPT-Researcher configs × 8 topics")
    parser.add_argument(
        "--configs", nargs="+",
        default=[c["name"] for c in CONFIGS],
        choices=[c["name"] for c in CONFIGS],
        help="Which configs to run (default: all 4)",
    )
    parser.add_argument(
        "--no-llm-metrics", action="store_true",
        help="Skip subtopic_coverage and unsupported_claim (~$0.04/query saved)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip configs that already have a log file",
    )
    parser.add_argument(
        "--summary-only", action="store_true",
        help="Print summary from existing logs without running anything",
    )
    parser.add_argument(
        "--max-topics", type=int, default=None,
        help="Limit to first N topics (smoke-testing a config cheaply)",
    )
    parser.add_argument(
        "--compare", nargs=2, metavar=("LOG_A", "LOG_B"),
        help="Diff two existing log files (before/after) and exit; needs no API keys",
    )
    parser.add_argument(
        "--detail", action="store_true",
        help="With --compare: also show a per-query breakdown",
    )
    args = parser.parse_args()

    # --compare is a pure log diff — no researcher, no API keys, no event loop.
    if args.compare:
        compare_logs(args.compare[0], args.compare[1], detail=args.detail)
        sys.exit(0)

    # Load API keys from file if not in environment
    if not os.getenv("OPENAI_API_KEY"):
        key_path = Path("D:/chenh/api_keys/gpt_api_key.txt")
        if key_path.exists():
            os.environ["OPENAI_API_KEY"] = key_path.read_text().strip()

    if not os.getenv("TAVILY_API_KEY"):
        key_path = Path("D:/chenh/api_keys/tavily_api_key.txt")
        if key_path.exists():
            os.environ["TAVILY_API_KEY"] = key_path.read_text().strip()

    try:
        asyncio.run(main(
            config_names=args.configs,
            run_llm_metrics=not args.no_llm_metrics,
            resume=args.resume,
            summary_only=args.summary_only,
            max_topics=args.max_topics,
        ))
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"Fatal: {e}")
        raise
