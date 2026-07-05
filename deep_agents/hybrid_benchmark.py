"""Hybrid-research benchmark: private documents + web vs web-only tooling.

This measures the capability gap, not a percentage-point gap: a deep agent
whose only research tool is raw web search cannot research an organization's
private documents at all. GPT Researcher's ``hybrid`` mode runs the same
pipeline over local documents (via DOC_PATH) and the web simultaneously.

Setup: a corpus of fictional internal company documents (Veltrix Dynamics, an
invented AMR robotics company - so no fact can leak from the public web) lives
in ``benchmark_data/internal_docs/``. Both agents receive the identical brief:
a due-diligence report combining internal company facts with real market
context. Checkpoints are split into:

- internal: facts stated only in the private corpus (funding, pricing, fleet
  metrics, roadmap)
- web: real-world market facts verified from public sources (competitor
  funding/IPO status)

Each report is graded per checkpoint (CORRECT/PARTIAL/MISSING/WRONG) by an
LLM judging only consistency with the provided ground truth. The headline
metric is internal-checkpoint coverage: web-only tooling should score ~0.

Usage (from the repository root):
    python deep_agents/hybrid_benchmark.py
"""

from dotenv import load_dotenv
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

DOCS_DIR = Path(__file__).parent / "benchmark_data" / "internal_docs"
os.environ["DOC_PATH"] = str(DOCS_DIR)

from langchain_openai import ChatOpenAI

from deep_agents.benchmark import build_baseline_agent, build_gptr_agent
from deep_agents.report_benchmark import write_report
from deep_agents.recency_benchmark import grade_report

RESULTS_DIR = Path(__file__).parent / "benchmark_results"

TASK = {
    "id": "veltrix_dd",
    "prompt": (
        "You are preparing a due-diligence brief on Veltrix Dynamics B.V., a "
        "Rotterdam-based warehouse robotics (AMR) company we are evaluating. "
        "Internal company documents are available to your research tools if "
        "they support document research. Write a brief covering: (1) the "
        "company's funding history and current financial trajectory, (2) its "
        "product line and 2026 roadmap including pricing, (3) operational "
        "performance and key risks, and (4) how it is positioned against the "
        "current competitive landscape in warehouse AMRs (Geek+, Locus "
        "Robotics, Exotec), using up-to-date market facts. Be specific about "
        "numbers, dates and names, and cite your sources."
    ),
    # Facts that exist ONLY in the private corpus.
    "internal_checkpoints": [
        "Veltrix has raised $142M total, most recently an $85M Series C in October 2025 led by Meridian Growth Partners at a $610M post-money valuation.",
        "Q1 2026 revenue was $21.4M (+67% YoY) with RaaS ARR of $46.9M; the 2026 revenue target is $96M.",
        "The current VLX-400 lists at $48,500 per robot, with RaaS at $1,950 per robot per month.",
        "The VLX-500 launches in Q4 2026 at a $56,000 list price, with 950 kg payload and a -30°C cold rating.",
        "The deployed fleet is 3,120 robots across 47 sites, with 99.2% availability in Q1 2026.",
        "Key risks include customer concentration (top 3 customers = 44% of ARR) and the VLX-500's solid-state LiDAR cold-chamber certification (in test cycle 2 of 3), which could slip the launch to Q2 2027.",
        "Veltrix's moat is cold-chain: certified operation down to -25°C today, 61% of ARR from frozen/chilled distribution centers, and a 71% win rate in cold-chain RFPs.",
        "A February 11, 2026 firmware regression (v4.7.2) caused localization drift at 14 sites and was resolved within 36 hours with no SLA penalties.",
    ],
    # Real-world market facts verified from public sources (July 2026).
    "web_checkpoints": [
        "Geek+ (Geekplus) went public on the Hong Kong Stock Exchange in July 2025 - the first IPO in the AMR warehouse robotics market - raising roughly $280M at about a $2.8B market cap.",
        "Geek+ is the global warehouse-fulfillment AMR market share leader by revenue (per Interact Analysis, for roughly seven consecutive years).",
        "Locus Robotics remains private, with total funding of roughly $410-440M and 13,000+ robots deployed.",
        "Exotec is a French warehouse robotics unicorn known for its Skypod ASRS system and remains private (roughly $446M raised).",
    ],
    "official_domains": [],
}


def coverage(grades: list[dict]) -> dict:
    gs = [g["grade"] for g in grades]
    n = len(gs)
    return {
        "correct": gs.count("CORRECT"),
        "partial": gs.count("PARTIAL"),
        "missing": gs.count("MISSING"),
        "wrong": gs.count("WRONG"),
        "coverage": round((gs.count("CORRECT") + 0.5 * gs.count("PARTIAL")) / n, 3) if n else 0.0,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Hybrid-research benchmark: private docs + web vs web-only")
    parser.add_argument("--model", type=str, default=os.environ.get("STRATEGIC_LLM", "openai:gpt-5.4"))
    parser.add_argument("--grader-model", type=str, default="gpt-5.4")
    args = parser.parse_args()

    grader = ChatOpenAI(model=args.grader_model)
    baseline_agent, _ = build_baseline_agent(args.model)
    gptr_agent, gptr_costs = build_gptr_agent(args.model, source="hybrid")

    print(f"Hybrid benchmark: model {args.model}, grader {args.grader_model}")
    print(f"Internal corpus: {DOCS_DIR}\n")

    record = {"task": TASK["id"], "prompt": TASK["prompt"]}
    for system, agent in (("baseline", baseline_agent), ("gptr", gptr_agent)):
        print(f"[{system}] writing...")
        outcome = await write_report(agent, TASK["prompt"])
        internal = await asyncio.to_thread(
            grade_report, grader, {"checkpoints": TASK["internal_checkpoints"]}, outcome["report"]
        )
        web = await asyncio.to_thread(
            grade_report, grader, {"checkpoints": TASK["web_checkpoints"]}, outcome["report"]
        )
        record[system] = {
            "report": outcome["report"],
            "latency_seconds": outcome["latency_seconds"],
            "internal_grades": internal,
            "web_grades": web,
            "internal": coverage(internal),
            "web": coverage(web),
        }
        print(f"[{system}] internal: {record[system]['internal']}")
        print(f"[{system}] web:      {record[system]['web']}")

    summary = {
        s: {
            "internal_coverage": record[s]["internal"]["coverage"],
            "web_coverage": record[s]["web"]["coverage"],
            "latency_seconds": record[s]["latency_seconds"],
        }
        for s in ("baseline", "gptr")
    }
    summary["gptr_internal_cost_usd"] = round(gptr_costs.get("total", 0.0), 4)
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))

    RESULTS_DIR.mkdir(exist_ok=True)
    results_path = RESULTS_DIR / f"hybrid_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({
            "run_metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": args.model,
                "grader_model": args.grader_model,
                "doc_path": str(DOCS_DIR),
            },
            "summary": summary,
            "records": [record],
        }, f, indent=2)
    print(f"\nResults saved to {results_path}")


if __name__ == "__main__":
    asyncio.run(main())
