"""
Quality Evaluation Runner
--------------------------
Runs GPT-Researcher on a set of queries and evaluates each report across
six quality metrics:

  - Citation Ratio        : used sources cited in the report            ($0)
  - Source Diversity      : domain variety (ratio + Shannon entropy)     ($0)
  - Source Authority      : heuristic + optional LLM authority score     ($0 / ~$0.01/q)
  - Subtopic Coverage     : LLM-judged coverage of expected subtopics (~$0.02/q)
  - Hallucination         : binary faithfulness check vs sources       (~$0.01/q)
  - Unsupported Claim Rate: fraction of claims lacking source support  (~$0.02/q)

Usage:
    python -m evals.quality_eval.run_eval --num_examples 5
    python -m evals.quality_eval.run_eval --num_examples 10 --no-subtopic
    python -m evals.quality_eval.run_eval --num_examples 10 --no-hallucination
    python -m evals.quality_eval.run_eval --num_examples 10 --no-unsupported-claim
    python -m evals.quality_eval.run_eval --num_examples 10 --no-subtopic --no-hallucination --no-unsupported-claim
"""

import asyncio
import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from gpt_researcher.agent import GPTResearcher
from gpt_researcher.utils.enum import ReportType, ReportSource, Tone

from evals.quality_eval.metrics import evaluate_report, skipped as _skipped, is_skipped as _is_skipped

try:
    from evals.hallucination_eval.evaluate import HallucinationEvaluator
    _HALLUCINATION_AVAILABLE = True
except ImportError:
    _HALLUCINATION_AVAILABLE = False

GRADER_MODEL_NAME = "gpt-4-turbo"
LOGS_DIR = Path(__file__).parent / "logs"
QUERIES_FILE = Path(__file__).parent.parent / "hallucination_eval" / "inputs" / "search_queries.jsonl"


def _get_git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return "unknown"


def _load_queries(n: int) -> list[str]:
    import random
    queries = []
    with open(QUERIES_FILE, encoding="utf-8") as f:
        for line in f:
            data = json.loads(line.strip())
            queries.append(data["question"])
    return random.sample(queries, min(n, len(queries)))


def _check_env():
    load_dotenv()
    missing = [v for v in ["OPENAI_API_KEY", "TAVILY_API_KEY"] if not os.getenv(v)]
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")


async def evaluate_single_query(
    query: str,
    grader_model,
    run_subtopic: bool,
    run_hallucination: bool,
    run_unsupported_claim: bool,
) -> dict:
    print(f"\n>> Query: {query}")
    t_start = time.perf_counter()

    researcher = GPTResearcher(
        query=query,
        report_type=ReportType.ResearchReport.value,
        report_format="markdown",
        report_source=ReportSource.Web.value,
        tone=Tone.Objective,
        verbose=False,
    )
    context  = await researcher.conduct_research()
    report   = await researcher.write_report()
    sources  = researcher.get_source_urls()
    cost     = researcher.get_costs()
    latency  = round(time.perf_counter() - t_start, 2)

    m = await evaluate_report(
        report, sources, context, query, grader_model,
        run_subtopic=run_subtopic, run_unsupported=run_unsupported_claim,
    )
    citation    = m["citation_faithfulness"]
    diversity   = m["source_diversity"]
    authority   = m["source_authority"]
    subtopic    = m["subtopic_coverage"]
    unsupported = m["unsupported_claim"]

    # --- LLM metric: hallucination (optional, requires `judges` library) ---
    if run_hallucination:
        if not _HALLUCINATION_AVAILABLE:
            hallucination = _skipped("judges library not installed — run: pip install judges")
        elif not context:
            hallucination = _skipped("no source context available")
        else:
            try:
                source_text = context if isinstance(context, str) else json.dumps(context)
                h_eval = HallucinationEvaluator()
                h_raw  = h_eval.evaluate_response(
                    model_output=report,
                    source_text=source_text[:8000],
                )
                hallucination = {
                    "is_hallucination": h_raw.get("is_hallucination"),
                    "reasoning":        h_raw.get("reasoning"),
                }
            except Exception as e:
                hallucination = _skipped(str(e))
    else:
        hallucination = None

    result = {
        "query":             query,
        "latency_seconds":   latency,
        "cost":              cost,
        "source_count":      len(sources),
        "report_length":     len(report),
        "citation_faithfulness": citation,
        "source_diversity":  diversity,
        "source_authority":  authority,
        "subtopic_coverage": subtopic,
        "hallucination":     hallucination,
        "unsupported_claim": unsupported,
    }

    # --- Console output ---
    def _fmt_metric(label, value, fmt_fn):
        if _is_skipped(value):
            print(f"   {label:<24} SKIPPED ({value['reason']})")
        else:
            fmt_fn(value)

    _fmt_metric("citation_faithful:", citation, lambda v:
        print(f"   citation_faithful:       "
              + (f"{v['citation_faithfulness']:.2f}"
                 if v.get('citation_faithfulness') is not None else 'n/a')
              + f"  ({len(v['listed_only_domains'])} listed-only)"))
    _fmt_metric("diversity_ratio:", diversity, lambda v:
        print(f"   diversity_ratio:         {v['diversity_ratio']:.2f}  "
              f"entropy={v['domain_entropy']:.2f}"))
    _fmt_metric("authority_score:", authority, lambda v:
        print(f"   authority_score:         {v['avg_authority_score']:.2f}"))

    if subtopic is not None:
        _fmt_metric("subtopic_coverage:", subtopic, lambda v:
            print(f"   subtopic_coverage:       "
                  + (f"{v['subtopic_coverage_rate']:.2f}"
                     if v.get('subtopic_coverage_rate') is not None else "ERROR")))

    if hallucination is not None:
        _fmt_metric("hallucination:", hallucination, lambda v:
            print(f"   hallucination:           {'YES' if v.get('is_hallucination') else 'NO'}"))

    if unsupported is not None:
        _fmt_metric("avg_claim_score:", unsupported, lambda v:
            print(f"   avg_claim_score:         {v.get('avg_claim_score', 0):.2f}  "
                  f"(unsupported={v.get('unsupported_claim_rate', 0):.2f}  "
                  f"inferred={v.get('inferred_claim_rate', 0):.2f}  "
                  f"n={v.get('total_claims', 0)})"))

    print(f"   latency={latency}s  cost=${cost:.4f}")

    return result


async def main(num_examples: int, run_subtopic: bool, run_hallucination: bool, run_unsupported_claim: bool):
    _check_env()

    run_start     = time.perf_counter()
    run_timestamp = datetime.now(timezone.utc).isoformat()
    grader_model  = ChatOpenAI(
        temperature=0,
        model_name=GRADER_MODEL_NAME,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    if run_hallucination and not _HALLUCINATION_AVAILABLE:
        print("Warning: judges library not installed — hallucination metric will be skipped.")
        print("         Install with: pip install judges\n")

    queries = _load_queries(num_examples)
    print(f"Quality eval: {len(queries)} queries  "
          f"subtopic={'on' if run_subtopic else 'off'}  "
          f"hallucination={'on' if run_hallucination else 'off'}  "
          f"unsupported_claim={'on' if run_unsupported_claim else 'off'}\n")

    results = []
    for query in queries:
        try:
            r = await evaluate_single_query(
                query, grader_model, run_subtopic, run_hallucination, run_unsupported_claim
            )
            results.append(r)
        except Exception as e:
            print(f"   [ERROR] {e}")
            results.append({"query": query, "error": str(e)})

    successful = [r for r in results if "error" not in r]
    n = len(successful)

    if n == 0:
        print("No successful results.")
        return

    # --- Aggregate ---
    def avg(key_path):
        vals = []
        for r in successful:
            obj = r
            for k in key_path:
                obj = obj.get(k) if isinstance(obj, dict) else None
            # Skip None and skipped-sentinel values
            if obj is not None and not _is_skipped(obj):
                vals.append(obj)
        return round(sum(vals) / len(vals), 3) if vals else None

    # hallucination_rate: proportion of queries where hallucination was detected
    hallucinated = [
        r for r in successful
        if r.get("hallucination") and r["hallucination"].get("is_hallucination") is True
    ]
    evaluated_for_hallucination = [
        r for r in successful
        if r.get("hallucination") and r["hallucination"].get("is_hallucination") is not None
    ]
    # TODO: hallucination detection itself might be wrong, need refinement
    hallucination_rate = (
        round(len(hallucinated) / len(evaluated_for_hallucination), 3)
        if evaluated_for_hallucination else None
    )

    aggregate = {
        "avg_citation_faithfulness":  avg(["citation_faithfulness", "citation_faithfulness"]),
        "avg_diversity_ratio":        avg(["source_diversity",   "diversity_ratio"]),
        "avg_domain_entropy":         avg(["source_diversity",   "domain_entropy"]),
        "avg_authority_score":        avg(["source_authority",   "avg_authority_score"]),
        "avg_subtopic_coverage_rate": avg(["subtopic_coverage",  "subtopic_coverage_rate"]),
        "hallucination_rate":              hallucination_rate,
        "avg_claim_score":                 avg(["unsupported_claim", "avg_claim_score"]),
        "avg_unsupported_claim_rate":     avg(["unsupported_claim", "unsupported_claim_rate"]),
        "avg_inferred_claim_rate":        avg(["unsupported_claim", "inferred_claim_rate"]),
        "avg_latency_seconds":             avg(["latency_seconds"]),
        "avg_cost":                   avg(["cost"]),
        "successful":                 n,
        "failed":                     len(results) - n,
    }

    print("\n=== QUALITY EVAL SUMMARY ===")
    for k, v in aggregate.items():
        print(f"  {k}: {v}")

    # --- Save log ---
    LOGS_DIR.mkdir(exist_ok=True)
    log = {
        "run_metadata": {
            "timestamp":            run_timestamp,
            "git_commit":           _get_git_commit(),
            "grader_model":         GRADER_MODEL_NAME,
            "researcher_model":     os.getenv("SMART_LLM", "openai:gpt-4.1"),
            "num_examples":         num_examples,
            "subtopic_enabled":       run_subtopic,
            "hallucination_enabled":       run_hallucination,
            "unsupported_claim_enabled":   run_unsupported_claim,
            "total_duration_seconds": round(time.perf_counter() - run_start, 2),
        },
        "aggregate_metrics": aggregate,
        "results": results,
    }
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = LOGS_DIR / f"quality_eval_{ts}_n{num_examples}.jsonl"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(log) + "\n")
    print(f"\nLog saved: {log_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GPT-Researcher quality evaluation")
    parser.add_argument("--num_examples", type=int, default=5,
                        help="Number of queries to evaluate (default: 5)")
    parser.add_argument("--no-subtopic", action="store_true",
                        help="Skip subtopic_coverage (saves ~$0.02/query)")
    parser.add_argument("--no-hallucination", action="store_true",
                        help="Skip hallucination check (requires: pip install judges)")
    parser.add_argument("--no-unsupported-claim", action="store_true",
                        help="Skip unsupported claim rate (~$0.02/query)")
    args = parser.parse_args()

    try:
        asyncio.run(main(
            args.num_examples,
            run_subtopic=not args.no_subtopic,
            run_hallucination=not args.no_hallucination,
            run_unsupported_claim=not args.no_unsupported_claim,
        ))
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"Fatal error: {e}")
        raise
