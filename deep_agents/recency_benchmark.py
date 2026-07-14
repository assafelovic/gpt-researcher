"""Recency benchmark: deep agent + GPT Researcher vs deep agent + raw search.

Measures what matters for real-world research: whether an agent's report about
fast-moving topics is CURRENT and CORRECT. Tasks spread across domains where
the ground truth changed after the model's training cutoff - software releases,
AI model pricing, live sports tournaments, awards season, and spaceflight -
each with a rubric of checkpoints verified from official sources at
benchmark-authoring time (July 2026).

Each report is graded per checkpoint by an LLM that judges ONLY consistency
between the report and the provided ground truth (so the grader's own training
cutoff does not matter):

- CORRECT: the report states the checkpoint fact (or consistent specifics)
- PARTIAL: addressed but incomplete or vague
- MISSING: not addressed
- WRONG: the report contradicts the checkpoint (stale or hallucinated info)

Headline metrics per system: checkpoint coverage, stale/wrong count (the
killer metric), and the share of citations pointing at official documentation
domains.

Usage (from the repository root):
    python deep_agents/recency_benchmark.py --concurrency 2
"""

from dotenv import load_dotenv
import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

from langchain_openai import ChatOpenAI

from deep_agents.benchmark import build_baseline_agent, build_gptr_agent, message_text
from deep_agents.report_benchmark import URL_PATTERN, write_report

RESULTS_DIR = Path(__file__).parent / "benchmark_results"

# Ground truth verified from official sources on 2026-07-04. Each checkpoint
# is a fact the report should state; WRONG means the report contradicts it.
TASKS = [
    {
        "id": "deepagents",
        "domain": "tech",
        "prompt": (
            "Write a design brief for our engineering team on building a research "
            "assistant with the deepagents Python library (latest version as of now). "
            "Cover: the current version, the core API for creating an agent, filesystem "
            "backends, how to define subagents, and human-in-the-loop support. "
            "Be specific about package versions, function and parameter names."
        ),
        "official_domains": ["docs.langchain.com", "pypi.org", "github.com", "langchain.com"],
        "checkpoints": [
            "The current deepagents release line is 0.6.x (0.6.12 as of July 2026); stating a much older version (e.g. 0.3.x) as current is wrong.",
            "Agents are created with create_deep_agent(), passing model, tools, and system_prompt.",
            "The harness has a built-in write_todos planning tool and a built-in task tool for spawning subagents.",
            "Custom subagents are passed via the subagents= parameter as dicts with name, description, system_prompt (and optionally tools/model), or as CompiledSubAgent for prebuilt graphs.",
            "The virtual filesystem has pluggable backends: state-backed by default (StateBackend), FilesystemBackend(root_dir=..., virtual_mode=True) for local disk, StoreBackend for durable stores.",
            "Human-in-the-loop is configured with the interrupt_on parameter mapping tool names to interrupt configs.",
        ],
    },
    {
        "id": "openai_models",
        "domain": "tech",
        "prompt": (
            "Write a cost-planning brief for our engineering team on OpenAI's current "
            "model lineup and API pricing as of mid-2026, to guide model selection. "
            "Cover the flagship and mid-tier models, exact API model names, per-token "
            "pricing, and reasoning-effort options. Be specific and current."
        ),
        "official_domains": ["openai.com", "developers.openai.com", "platform.openai.com"],
        "checkpoints": [
            "GPT-5.5 is the current flagship, available in the API since late April 2026 (announced/released April 24, 2026).",
            "gpt-5.5 API pricing is $5 per 1M input tokens and $30 per 1M output tokens.",
            "gpt-5.5-pro exists as a higher-accuracy variant priced at $30 per 1M input / $180 per 1M output tokens.",
            "The GPT-5.4 family (released March 2026) is the mid-tier: gpt-5.4 costs $2.50 per 1M input / $15 per 1M output tokens.",
            "gpt-5.4-mini costs $0.75 per 1M input / $4.50 per 1M output tokens (and gpt-5.4-nano $0.20 / $1.25).",
            "Newest models support a reasoning-effort parameter with levels up to xhigh.",
        ],
    },
    {
        "id": "nextjs16",
        "domain": "tech",
        "prompt": (
            "Write a migration guide for our engineering team: upgrading a production "
            "app from Next.js 15 to the current Next.js as of mid-2026. Cover the "
            "current version status, runtime requirements, breaking changes, and new "
            "build tooling defaults. Be specific about versions and API names."
        ),
        "official_domains": ["nextjs.org", "vercel.com", "github.com", "rc.nextjs.org"],
        "checkpoints": [
            "The current stable major is Next.js 16, with 16.3 in preview (announced late June 2026); presenting Next.js 14 or 15 as the latest is wrong.",
            "Next.js 16 requires Node.js 20.9+ (Node 18 no longer supported) and TypeScript 5.1+.",
            "Synchronous access to request APIs (cookies(), headers(), params) is fully removed in 16 - they are async-only.",
            "The middleware.js filename/convention is deprecated and renamed to proxy.",
            "Turbopack in 16.x has persistent file-system caching and (in 16.3) default memory eviction; persistent build cache is opt-in via turbopackFileSystemCacheForBuild.",
            "Next.js 16 pairs with React 19.2, and the next lint command has been removed.",
        ],
    },
    {
        "id": "worldcup2026",
        "domain": "current_events",
        "prompt": (
            "Write a briefing for a sports desk on the state of the 2026 FIFA World "
            "Cup as of today. Cover the tournament format, how the knockout stage "
            "has unfolded so far including notable results and upsets, which teams "
            "have advanced to the current round, and the upcoming fixtures. Be "
            "specific about scores, dates, and match-ups."
        ),
        "official_domains": ["fifa.com", "espn.com", "bbc.com", "bbc.co.uk"],
        "checkpoints": [
            "The 2026 World Cup is the expanded 48-team format co-hosted by the USA, Canada, and Mexico, and as of July 4, 2026 the Round of 32 is complete and the Round of 16 is underway.",
            "All three co-hosts reached the Round of 16: the USA beat Bosnia and Herzegovina 2-0, Mexico beat Ecuador 2-0, and Canada beat South Africa 1-0.",
            "Germany and the Netherlands were both eliminated in the Round of 32 on penalties (Germany by Paraguay after 1-1, the Netherlands by Morocco after 1-1).",
            "Defending champions Argentina needed extra time to beat Cape Verde 3-2 in the Round of 32 on July 3.",
            "Egypt eliminated Australia on penalties (4-2 after a 1-1 draw) and face Argentina in the Round of 16.",
            "Round of 16 fixtures include Canada vs Morocco and France vs Paraguay on July 4, Spain vs Portugal on July 6, and Belgium vs the USA on July 6.",
        ],
    },
    {
        "id": "us_sports_2026",
        "domain": "current_events",
        "prompt": (
            "Write a recap for a sports desk of the two marquee US championships of "
            "the 2025-26 season: Super Bowl LX and the 2026 NBA Finals. Cover who "
            "played, the final scores and series results, the MVPs, and what made "
            "each outcome historically significant. Be specific about dates and "
            "numbers."
        ),
        "official_domains": ["nfl.com", "nba.com", "espn.com", "apnews.com"],
        "checkpoints": [
            "The Seattle Seahawks won Super Bowl LX, beating the New England Patriots 29-13 on February 8, 2026, at Levi's Stadium - the franchise's second Super Bowl title.",
            "Kenneth Walker III was named Super Bowl LX MVP, and Seattle's defense sealed the game with a fourth-quarter interception returned for a touchdown.",
            "The New York Knicks won the 2026 NBA Finals, beating the San Antonio Spurs 4-1 - their first NBA championship since 1973.",
            "The Knicks clinched the title with a 94-90 win in Game 5 on June 13, 2026, coming back from double-digit deficits in all four of their series wins.",
            "Jalen Brunson was named NBA Finals MVP, scoring 45 points in the closeout Game 5.",
            "The Spurs reached the Finals by beating the Thunder 4-3 in the Western Conference finals, while the Knicks swept the Cavaliers 4-0 in the East.",
        ],
    },
    {
        "id": "oscars2026",
        "domain": "current_events",
        "prompt": (
            "Write a wrap-up for an entertainment desk on the 98th Academy Awards "
            "(the 2026 Oscars). Cover when and where the ceremony took place, who "
            "hosted, the winners in the major categories, and which films dominated "
            "the night. Be specific about names, films, and award counts."
        ),
        "official_domains": ["oscars.org", "deadline.com", "variety.com", "hollywoodreporter.com"],
        "checkpoints": [
            "The 98th Academy Awards took place on March 15, 2026, at the Dolby Theatre in Hollywood, hosted by Conan O'Brien.",
            "One Battle After Another won Best Picture and led the night with six awards, with Paul Thomas Anderson winning Best Director and Best Adapted Screenplay.",
            "Michael B. Jordan won Best Actor for his dual role in Sinners - his first Academy Award nomination and win.",
            "Jessie Buckley won Best Actress for Hamnet.",
            "Sean Penn won Best Supporting Actor for One Battle After Another and Amy Madigan won Best Supporting Actress for Weapons.",
            "Sinners led all films with 16 nominations and won four awards, including Best Original Screenplay for Ryan Coogler; KPop Demon Hunters won Best Animated Feature and Best Original Song for 'Golden'.",
        ],
    },
    {
        "id": "artemis2",
        "domain": "current_events",
        "prompt": (
            "Write a mission summary for a science desk on NASA's Artemis II mission. "
            "Cover when it launched and returned, the crew and the historic firsts "
            "they represent, what the mission accomplished, any records set, and "
            "what it means for the Artemis program going forward. Be specific about "
            "dates, names, and figures."
        ),
        "official_domains": ["nasa.gov", "esa.int", "asc-csa.gc.ca"],
        "checkpoints": [
            "Artemis II launched on April 1, 2026, on the SLS rocket from Kennedy Space Center - the first crewed mission to the Moon since Apollo 17 in 1972.",
            "The crew was Reid Wiseman (commander), Victor Glover (pilot), Christina Koch, and CSA astronaut Jeremy Hansen - with Glover the first Black person, Koch the first woman, and Hansen the first Canadian to travel to the Moon.",
            "It was a roughly 10-day crewed lunar flyby (not a landing) that splashed down in the Pacific off San Diego on April 10, 2026.",
            "The crew set the record for the farthest humans have traveled from Earth - 252,756 miles, surpassing Apollo 13's 1970 record.",
            "The mission validated the Orion spacecraft with crew aboard, including the critical translunar injection burn and high-speed (~25,000 mph) reentry.",
            "The mission was declared a success and paves the way for Artemis III, the program's lunar landing mission.",
        ],
    },
]

GRADER_TEMPLATE = """You are grading a technical report against ground-truth \
checkpoints. The ground truth below was verified from official sources and is \
authoritative - judge ONLY whether the report is consistent with it. Ignore \
your own knowledge if it conflicts with the ground truth.

For each checkpoint, grade the report as:
- CORRECT: the report states the checkpoint fact, or gives specifics fully consistent with it
- PARTIAL: the report addresses the topic but is incomplete or vague on the fact
- MISSING: the report does not address the topic of this checkpoint
- WRONG: the report makes a claim that CONTRADICTS the checkpoint (e.g. states an older version as current, wrong price, deprecated API as current practice)

Checkpoints:
{checkpoints}

=== REPORT ===
{report}
=== END REPORT ===

Reply with JSON only, no other text: an array with one object per checkpoint in \
order: [{{"checkpoint": 1, "grade": "CORRECT|PARTIAL|MISSING|WRONG", "evidence": "short quote or note"}}, ...]"""


def official_citation_share(report: str, official_domains: list[str]) -> dict:
    urls = {u.rstrip(".,;") for u in URL_PATTERN.findall(report or "")}
    domains = [urlparse(u).netloc.removeprefix("www.") for u in urls if urlparse(u).netloc]
    official = [d for d in domains if any(d == od or d.endswith("." + od) for od in official_domains)]
    return {
        "unique_cited_urls": len(urls),
        "official_citations": len(official),
        "official_share": round(len(official) / len(domains), 2) if domains else 0.0,
    }


def grade_report(grader, task: dict, report: str) -> list[dict]:
    checkpoints_text = "\n".join(f"{i}. {c}" for i, c in enumerate(task["checkpoints"], 1))
    prompt = GRADER_TEMPLATE.format(checkpoints=checkpoints_text, report=report or "(empty report)")
    for _ in range(3):
        response = grader.invoke([{"role": "user", "content": prompt}]).content.strip()
        # Extract the JSON array even if the model wraps it in prose/fences
        start, end = response.find("["), response.rfind("]")
        if start != -1 and end > start:
            try:
                grades = json.loads(response[start:end + 1])
                if len(grades) == len(task["checkpoints"]):
                    return grades
            except json.JSONDecodeError:
                pass
    raise RuntimeError(f"Grader returned unparseable output after 3 attempts: {response[:200]}")


def summarize(records: list[dict], system: str) -> dict:
    grades = [g["grade"] for r in records for g in r[system]["grades"]]
    n = len(grades)
    coverage = (grades.count("CORRECT") + 0.5 * grades.count("PARTIAL")) / n if n else 0.0
    by_domain = {}
    for domain in sorted({r["domain"] for r in records}):
        domain_grades = [g["grade"] for r in records if r["domain"] == domain for g in r[system]["grades"]]
        dn = len(domain_grades)
        by_domain[domain] = {
            "coverage": round((domain_grades.count("CORRECT") + 0.5 * domain_grades.count("PARTIAL")) / dn, 3) if dn else 0.0,
            "wrong_stale": domain_grades.count("WRONG"),
        }
    return {
        "checkpoints_total": n,
        "correct": grades.count("CORRECT"),
        "partial": grades.count("PARTIAL"),
        "missing": grades.count("MISSING"),
        "wrong_stale": grades.count("WRONG"),
        "coverage": round(coverage, 3),
        "by_domain": by_domain,
        "avg_official_share": round(sum(r[system]["citations"]["official_share"] for r in records) / len(records), 2),
        "avg_unique_cited_urls": round(sum(r[system]["citations"]["unique_cited_urls"] for r in records) / len(records), 1),
        "avg_latency_seconds": round(sum(r[system]["latency_seconds"] for r in records) / len(records), 1),
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Recency benchmark: GPT Researcher deep agent vs raw-search deep agent")
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--model", type=str, default=os.environ.get("STRATEGIC_LLM", "openai:gpt-5.4"))
    parser.add_argument("--grader-model", type=str, default="gpt-5.4")
    args = parser.parse_args()

    grader = ChatOpenAI(model=args.grader_model)
    baseline_agent, _ = build_baseline_agent(args.model)
    gptr_agent, gptr_costs = build_gptr_agent(args.model)

    print(f"Recency benchmark: {len(TASKS)} tasks, model {args.model}, grader {args.grader_model}\n")

    semaphore = asyncio.Semaphore(args.concurrency)

    async def run_task(task: dict) -> dict:
        async with semaphore:
            print(f"[{task['id']}] baseline writing...")
            baseline = await write_report(baseline_agent, task["prompt"])
            print(f"[{task['id']}] gptr writing...")
            gptr = await write_report(gptr_agent, task["prompt"])
        record = {"task": task["id"], "domain": task["domain"], "prompt": task["prompt"]}
        for system, outcome in (("baseline", baseline), ("gptr", gptr)):
            grades = await asyncio.to_thread(grade_report, grader, task, outcome["report"])
            record[system] = {
                "report": outcome["report"],
                "latency_seconds": outcome["latency_seconds"],
                "grades": grades,
                "citations": official_citation_share(outcome["report"], task["official_domains"]),
            }
            wrong = [g for g in grades if g["grade"] == "WRONG"]
            print(f"[{task['id']}] {system}: " + ", ".join(g["grade"] for g in grades) + (f"  WRONG: {[g['checkpoint'] for g in wrong]}" if wrong else ""))
        return record

    records = list(await asyncio.gather(*(run_task(t) for t in TASKS)))

    summary = {
        "baseline": summarize(records, "baseline"),
        "gptr": summarize(records, "gptr"),
        "gptr_internal_cost_usd": round(gptr_costs.get("total", 0.0), 4),
    }
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))

    RESULTS_DIR.mkdir(exist_ok=True)
    results_path = RESULTS_DIR / f"recency_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({
            "run_metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": args.model,
                "grader_model": args.grader_model,
                "ground_truth_verified": "2026-07-04",
            },
            "summary": summary,
            "records": records,
        }, f, indent=2)
    print(f"\nResults saved to {results_path}")


if __name__ == "__main__":
    asyncio.run(main())
