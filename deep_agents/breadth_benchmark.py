"""Breadth x depth benchmark: scattered-evidence briefs at fixed agent budgets.

The claim this measures: GPT Researcher gives a deep agent breadth AND depth
in one run. Each `deep_research` call fans out into parallel sub-queries,
scrapes dozens of pages, and returns one distilled, cited digest - so the
main agent covers a wide brief in a handful of steps. A raw-search agent must
instead pull every page through its own context window, one loop iteration at
a time.

To expose that difference, each task is a composite brief with 20+ verifiable
checkpoints scattered across unrelated domains and dozens of pages - no
single aggregator page covers even half of one task. Both agents run the
same brief at fixed agent-step budgets (LangGraph recursion limits), and each
report is graded per checkpoint (CORRECT/PARTIAL/MISSING/WRONG) against
ground truth verified from official sources on 2026-07-04.

Headline metric: checkpoint coverage at each step budget - i.e. how much
correct, current evidence each tooling extracts from the same orchestration
budget.

Usage (from the repository root):
    python deep_agents/breadth_benchmark.py --budgets 25 60
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

from langchain_openai import ChatOpenAI

from deep_agents.benchmark import build_baseline_agent, build_gptr_agent
from deep_agents.report_benchmark import URL_PATTERN, write_report
from deep_agents.recency_benchmark import grade_report

RESULTS_DIR = Path(__file__).parent / "benchmark_results"

# Ground truth verified from official sources on 2026-07-04.
TASKS = [
    {
        "id": "h1_2026_almanac",
        "prompt": (
            "Write a 'first half of 2026' almanac briefing for a newsroom: a "
            "single wide-coverage report on the defining events of January-July "
            "2026 across sports, entertainment and space. Cover: (1) the 2026 "
            "FIFA World Cup so far - format, hosts, how the knockout rounds have "
            "gone including specific results and upsets, and the upcoming "
            "round-of-16 schedule; (2) Super Bowl LX - teams, score, MVP, venue; "
            "(3) the 2026 NBA Finals - teams, series result, clinching game, "
            "MVP, historical significance; (4) the 98th Academy Awards - date, "
            "host, and winners across the major categories including the films "
            "that dominated; (5) NASA's Artemis II - dates, crew, records, "
            "outcome. Be specific about names, dates, scores and numbers "
            "throughout, and cite sources."
        ),
        "checkpoints": [
            # World Cup (8)
            "The 2026 World Cup is the expanded 48-team format co-hosted by the USA, Canada and Mexico; as of July 4 the Round of 32 is complete and the Round of 16 is underway.",
            "All three co-hosts reached the Round of 16: USA beat Bosnia and Herzegovina 2-0, Mexico beat Ecuador 2-0, Canada beat South Africa 1-0.",
            "Germany were eliminated in the Round of 32 by Paraguay on penalties (4-3 after a 1-1 draw).",
            "The Netherlands were eliminated in the Round of 32 by Morocco on penalties (3-2 after a 1-1 draw).",
            "Defending champions Argentina beat Cape Verde 3-2 after extra time in the Round of 32 on July 3.",
            "Egypt beat Australia on penalties (4-2 after 1-1) and face Argentina in the Round of 16 on July 7.",
            "Other Round of 32 results include France 3-0 Sweden, Spain 3-0 Austria, Portugal 2-1 Croatia, England 2-1 DR Congo and Belgium 3-2 Senegal (a.e.t.).",
            "Round of 16 fixtures include Canada vs Morocco and France vs Paraguay (July 4), Brazil vs Norway and Mexico vs England (July 5), Spain vs Portugal and Belgium vs USA (July 6).",
            # Super Bowl LX (4)
            "The Seattle Seahawks beat the New England Patriots 29-13 in Super Bowl LX on February 8, 2026.",
            "Super Bowl LX was played at Levi's Stadium in Santa Clara, and it was Seattle's second Super Bowl title.",
            "Kenneth Walker III was named Super Bowl LX MVP.",
            "Seattle's defense sealed the game with a fourth-quarter interception returned for a touchdown (by Uchenna Nwosu, 45 yards).",
            # NBA Finals (4)
            "The New York Knicks beat the San Antonio Spurs 4-1 in the 2026 NBA Finals - their first championship since 1973.",
            "The Knicks clinched with a 94-90 win in Game 5 on June 13, 2026, in San Antonio.",
            "Jalen Brunson was named Finals MVP, scoring 45 points in the closeout game.",
            "The Knicks came back from double-digit deficits in all four of their series wins (including 16 down in Game 5).",
            # Oscars (5)
            "The 98th Academy Awards took place on March 15, 2026, at the Dolby Theatre, hosted by Conan O'Brien.",
            "One Battle After Another won Best Picture and led the night with six awards; Paul Thomas Anderson won Best Director.",
            "Michael B. Jordan won Best Actor for Sinners; Jessie Buckley won Best Actress for Hamnet.",
            "Sean Penn won Best Supporting Actor (One Battle After Another); Amy Madigan won Best Supporting Actress (Weapons).",
            "Sinners led nominations with 16 and won four awards; KPop Demon Hunters won Best Animated Feature and Best Original Song ('Golden').",
            # Artemis II (4)
            "Artemis II launched April 1, 2026 - the first crewed Moon mission since Apollo 17 in 1972 - and splashed down in the Pacific on April 10.",
            "The crew: Reid Wiseman (commander), Victor Glover (pilot), Christina Koch and CSA astronaut Jeremy Hansen.",
            "The crew set the record for farthest humans from Earth: 252,756 miles, surpassing Apollo 13.",
            "It was a lunar flyby (no landing) that validated Orion with crew aboard, paving the way for the Artemis III landing.",
        ],
    },
    {
        "id": "ai_software_landscape",
        "prompt": (
            "Write a 'state of the stack, mid-2026' briefing for a CTO: a single "
            "wide-coverage report on where the AI and web engineering ecosystem "
            "stands right now. Cover: (1) OpenAI's current API model lineup and "
            "pricing - flagship and mid-tier models, exact model names, per-token "
            "prices, reasoning options; (2) the LangChain 1.x ecosystem - current "
            "versions, the modern agent-building API, what replaced the legacy "
            "patterns, and the runtime layer; (3) the deepagents library - "
            "current version and its core APIs for agents, subagents, "
            "filesystem backends and human-in-the-loop; (4) Next.js - the "
            "current major version, runtime requirements, key breaking changes "
            "and build tooling. Be specific about versions, names and prices, "
            "and cite sources."
        ),
        "checkpoints": [
            # OpenAI (6)
            "GPT-5.5 is the current flagship, in the API since late April 2026.",
            "gpt-5.5 costs $5 per 1M input tokens and $30 per 1M output tokens.",
            "gpt-5.5-pro is the higher-accuracy variant at $30 per 1M input / $180 per 1M output.",
            "The GPT-5.4 family (March 2026) is the mid-tier: gpt-5.4 at $2.50 per 1M input / $15 per 1M output.",
            "gpt-5.4-mini costs $0.75 / $4.50 per 1M tokens and gpt-5.4-nano $0.20 / $1.25.",
            "Newest OpenAI models support a reasoning-effort parameter with levels up to xhigh.",
            # LangChain (5)
            "LangChain 1.x is current, with recent releases in the 1.3.x range as of mid-2026; 0.x is legacy.",
            "create_agent is the modern API for building agents in LangChain 1.x.",
            "Legacy patterns like initialize_agent and AgentExecutor are deprecated/replaced in 1.x.",
            "LangChain 1.x agents support a middleware mechanism for customization.",
            "LangGraph serves as the runtime layer for durable execution, streaming and human-in-the-loop.",
            # deepagents (5)
            "The current deepagents release line is 0.6.x (0.6.12 as of July 2026).",
            "Agents are created with create_deep_agent(), passing model, tools and system_prompt; the harness has built-in write_todos planning and a task tool for subagents.",
            "Custom subagents are passed via the subagents= parameter as dicts with name, description, system_prompt (and optionally tools/model).",
            "The virtual filesystem has pluggable backends: StateBackend by default, FilesystemBackend(root_dir=..., virtual_mode=True) for local disk, StoreBackend for durable stores.",
            "Human-in-the-loop is configured with the interrupt_on parameter mapping tool names to interrupt configs.",
            # Next.js (5)
            "The current stable major is Next.js 16, with 16.3 in preview (announced late June 2026).",
            "Next.js 16 requires Node.js 20.9+ and TypeScript 5.1+.",
            "Synchronous access to request APIs (cookies(), headers(), params) is fully removed in 16 - async-only.",
            "The middleware.js convention is deprecated/renamed to proxy.",
            "Turbopack in 16.x has persistent file-system caching, and Next.js 16 pairs with React 19.2; next lint was removed.",
        ],
    },
]


def summarize(records: list[dict], system: str, budget: int) -> dict:
    key = f"{system}@{budget}"
    grades = [g["grade"] for r in records for g in r[key]["grades"]]
    n = len(grades)
    return {
        "checkpoints_total": n,
        "correct": grades.count("CORRECT"),
        "partial": grades.count("PARTIAL"),
        "missing": grades.count("MISSING"),
        "wrong_stale": grades.count("WRONG"),
        "coverage": round((grades.count("CORRECT") + 0.5 * grades.count("PARTIAL")) / n, 3) if n else 0.0,
        "avg_unique_cited_urls": round(sum(r[key]["unique_cited_urls"] for r in records) / len(records), 1),
        "avg_latency_seconds": round(sum(r[key]["latency_seconds"] for r in records) / len(records), 1),
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Breadth x depth benchmark at fixed agent budgets")
    parser.add_argument("--budgets", type=int, nargs="+", default=[25, 60],
                        help="agent-step budgets (LangGraph recursion limits) to test")
    parser.add_argument("--model", type=str, default=os.environ.get("STRATEGIC_LLM", "openai:gpt-5.4"))
    parser.add_argument("--grader-model", type=str, default="gpt-5.4")
    parser.add_argument("--concurrency", type=int, default=2)
    args = parser.parse_args()

    grader = ChatOpenAI(model=args.grader_model)
    baseline_agent, _ = build_baseline_agent(args.model)
    gptr_agent, gptr_costs = build_gptr_agent(args.model)
    agents = {"baseline": baseline_agent, "gptr": gptr_agent}

    print(f"Breadth benchmark: {len(TASKS)} tasks x budgets {args.budgets}, model {args.model}\n")

    semaphore = asyncio.Semaphore(args.concurrency)

    async def run_one(task: dict, system: str, budget: int) -> tuple[str, str, int, dict]:
        async with semaphore:
            print(f"[{task['id']}] {system}@{budget} writing...")
            try:
                outcome = await write_report(agents[system], task["prompt"], recursion_limit=budget)
            except Exception as e:
                # Hitting the recursion limit without a final answer counts as
                # an empty report - that IS the budget result.
                print(f"[{task['id']}] {system}@{budget} failed: {type(e).__name__}")
                outcome = {"report": "", "latency_seconds": 0.0, "metrics": {}}
        grades = await asyncio.to_thread(grade_report, grader, task, outcome["report"])
        urls = {u.rstrip(".,;") for u in URL_PATTERN.findall(outcome["report"] or "")}
        gs = [g["grade"] for g in grades]
        cov = (gs.count("CORRECT") + 0.5 * gs.count("PARTIAL")) / len(gs)
        print(f"[{task['id']}] {system}@{budget}: coverage={cov:.2f} wrong={gs.count('WRONG')} urls={len(urls)}")
        return task["id"], system, budget, {
            "report": outcome["report"],
            "latency_seconds": outcome["latency_seconds"],
            "grades": grades,
            "unique_cited_urls": len(urls),
        }

    jobs = [run_one(task, system, budget)
            for task in TASKS for system in agents for budget in args.budgets]
    outcomes = await asyncio.gather(*jobs)

    records = []
    for task in TASKS:
        record = {"task": task["id"], "prompt": task["prompt"]}
        for task_id, system, budget, data in outcomes:
            if task_id == task["id"]:
                record[f"{system}@{budget}"] = data
        records.append(record)

    summary = {
        f"{system}@{budget}": summarize(records, system, budget)
        for system in agents for budget in args.budgets
    }
    summary["gptr_internal_cost_usd"] = round(gptr_costs.get("total", 0.0), 4)
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))

    RESULTS_DIR.mkdir(exist_ok=True)
    results_path = RESULTS_DIR / f"breadth_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({
            "run_metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": args.model,
                "grader_model": args.grader_model,
                "budgets": args.budgets,
                "ground_truth_verified": "2026-07-04",
            },
            "summary": summary,
            "records": records,
        }, f, indent=2)
    print(f"\nResults saved to {results_path}")


if __name__ == "__main__":
    asyncio.run(main())
