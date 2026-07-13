"""Report-quality benchmark: deep agent + GPT Researcher vs deep agent + raw search.

Short-form QA benchmarks (SimpleQA, FRAMES) measure point-fact lookup, which
is not what a research-report system is for. This benchmark measures the
actual deliverable: given the same research topics, both agents write a
report, and the reports are compared in three ways:

1. Hard metrics - unique cited URLs, unique cited domains, word count.
2. Blind pairwise LLM judging (A/B order randomized per topic and dimension)
   on the dimensions used by deep-research evaluations such as DeepResearch
   Bench (https://arxiv.org/abs/2506.11763): comprehensiveness & depth,
   source & citation quality, factual grounding, and overall usefulness.
3. Per-dimension win rates aggregated across topics.

The two systems are identical (model, harness, base prompt) except for their
research tooling:

- baseline: the deepagents quickstart setup - a raw Tavily `internet_search`
  tool.
- gptr: this example's setup - GPT Researcher exposed as `quick_search` and
  `deep_research` tools.

Usage (from the repository root):
    python deep_agents/report_benchmark.py --num-topics 8 --concurrency 2
"""

from dotenv import load_dotenv
import argparse
import asyncio
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

from langchain_openai import ChatOpenAI

from deep_agents.benchmark import build_baseline_agent, build_gptr_agent, message_text

RESULTS_DIR = Path(__file__).parent / "benchmark_results"

# Diverse research topics: analytical questions that warrant a researched,
# cited report rather than a one-line answer.
TOPICS = [
    "What are the leading approaches to carbon capture and storage, and how do they compare on cost and scalability?",
    "How has the global semiconductor supply chain changed since 2020, and what are the key dependencies and risks?",
    "What does the evidence say about the impact of remote work on productivity and employee wellbeing?",
    "What are the main competing battery chemistries for grid-scale energy storage, and what are their trade-offs?",
    "How are regulators in the US and EU approaching AI governance, and how do the two frameworks differ?",
    "What is the current state of mRNA vaccine technology beyond COVID-19, and which applications are most promising?",
    "What are the economic and environmental arguments for and against deep-sea mining?",
    "How is precision agriculture changing farming, and what evidence exists for its impact on yields and sustainability?",
    "What are the main obstacles to commercial fusion power, and how close are current projects to overcoming them?",
    "What does research show about the effectiveness of four-day work week trials around the world?",
]

REPORT_REQUEST = (
    "Write a well-researched, well-structured report on the following topic. "
    "Ground every claim in researched sources and cite them with URLs. "
    "Topic: {topic}"
)

JUDGE_DIMENSIONS = {
    "comprehensiveness": "Which report is more comprehensive and insightful - covers more of the important aspects of the topic, with more depth and specificity?",
    "citation_quality": "Which report grounds its claims better in cited sources - more claims backed by citations, higher-quality and more diverse sources?",
    "factual_grounding": "Which report is more trustworthy - fewer unsupported or speculative statements, claims traceable to sources?",
    "overall": "Overall, which report would be more useful to a professional who needs to understand this topic?",
}

JUDGE_TEMPLATE = """You are an expert evaluator of research reports. Two research \
assistants were given the same topic and wrote the reports below. Judge them on \
exactly one dimension:

{dimension_question}

Topic: {topic}

=== REPORT A ===
{report_a}

=== REPORT B ===
{report_b}

=== END OF REPORTS ===

Reply with exactly one letter: "A" if Report A is better on this dimension, \
"B" if Report B is better, or "T" if they are genuinely tied. Do not reply \
with anything else."""

URL_PATTERN = re.compile(r"https?://[^\s\)\]\>\"']+")


def hard_metrics(report: str) -> dict:
    urls = {u.rstrip(".,;") for u in URL_PATTERN.findall(report or "")}
    domains = {urlparse(u).netloc.removeprefix("www.") for u in urls if urlparse(u).netloc}
    return {
        "unique_cited_urls": len(urls),
        "unique_cited_domains": len(domains),
        "word_count": len((report or "").split()),
    }


async def write_report(agent, topic: str, recursion_limit: int = 60) -> dict:
    start = time.perf_counter()
    result = await asyncio.wait_for(
        agent.ainvoke(
            {"messages": [{"role": "user", "content": REPORT_REQUEST.format(topic=topic)}]},
            config={"recursion_limit": recursion_limit},
        ),
        timeout=1800,
    )
    report = message_text(result["messages"][-1])
    return {
        "report": report,
        "latency_seconds": round(time.perf_counter() - start, 1),
        "metrics": hard_metrics(report),
    }


def judge_pair(judge, topic: str, report_a: str, report_b: str, dimension_question: str) -> str:
    prompt = JUDGE_TEMPLATE.format(
        dimension_question=dimension_question,
        topic=topic,
        report_a=report_a,
        report_b=report_b,
    )
    response = judge.invoke([{"role": "user", "content": prompt}]).content.strip().upper()
    return response if response in ("A", "B", "T") else "T"


async def judge_topic(judge, topic: str, baseline_report: str, gptr_report: str, rng: random.Random) -> dict:
    verdicts = {}
    for dimension, question in JUDGE_DIMENSIONS.items():
        gptr_is_a = rng.random() < 0.5
        report_a, report_b = (gptr_report, baseline_report) if gptr_is_a else (baseline_report, gptr_report)
        letter = await asyncio.to_thread(judge_pair, judge, topic, report_a, report_b, question)
        if letter == "T":
            verdicts[dimension] = "tie"
        else:
            winner_is_a = letter == "A"
            verdicts[dimension] = "gptr" if winner_is_a == gptr_is_a else "baseline"
    return verdicts


async def main() -> None:
    parser = argparse.ArgumentParser(description="Report-quality benchmark: GPT Researcher deep agent vs raw-search deep agent")
    parser.add_argument("--num-topics", type=int, default=8)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model", type=str, default=os.environ.get("STRATEGIC_LLM", "openai:gpt-5.4"))
    parser.add_argument("--judge-model", type=str, default="gpt-5.4")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    topics = TOPICS[: args.num_topics]
    judge = ChatOpenAI(model=args.judge_model)

    baseline_agent, _ = build_baseline_agent(args.model)
    gptr_agent, gptr_costs = build_gptr_agent(args.model)

    print(f"Report benchmark: {len(topics)} topics, model {args.model}, judge {args.judge_model}\n")

    semaphore = asyncio.Semaphore(args.concurrency)

    async def run_topic(index: int, topic: str) -> dict:
        async with semaphore:
            print(f"[{index + 1}/{len(topics)}] baseline writing: {topic[:60]}")
            baseline = await write_report(baseline_agent, topic)
            print(f"[{index + 1}/{len(topics)}] gptr writing: {topic[:60]}")
            gptr = await write_report(gptr_agent, topic)
        verdicts = await judge_topic(judge, topic, baseline["report"], gptr["report"], rng)
        print(f"[{index + 1}/{len(topics)}] verdicts: {verdicts}")
        return {"topic": topic, "baseline": baseline, "gptr": gptr, "verdicts": verdicts}

    records = list(await asyncio.gather(*(run_topic(i, t) for i, t in enumerate(topics))))

    summary = {"win_rates": {}, "hard_metrics_avg": {}}
    for dimension in JUDGE_DIMENSIONS:
        outcomes = [r["verdicts"][dimension] for r in records]
        summary["win_rates"][dimension] = {
            "gptr": outcomes.count("gptr"),
            "baseline": outcomes.count("baseline"),
            "tie": outcomes.count("tie"),
        }
    for system in ("baseline", "gptr"):
        n = len(records)
        summary["hard_metrics_avg"][system] = {
            "unique_cited_urls": round(sum(r[system]["metrics"]["unique_cited_urls"] for r in records) / n, 1),
            "unique_cited_domains": round(sum(r[system]["metrics"]["unique_cited_domains"] for r in records) / n, 1),
            "word_count": round(sum(r[system]["metrics"]["word_count"] for r in records) / n),
            "avg_latency_seconds": round(sum(r[system]["latency_seconds"] for r in records) / n, 1),
        }
    summary["gptr_internal_cost_usd"] = round(gptr_costs.get("total", 0.0), 4)

    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))

    RESULTS_DIR.mkdir(exist_ok=True)
    results_path = RESULTS_DIR / f"reports_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_n{len(topics)}.json"
    output = {
        "run_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "num_topics": len(topics),
            "seed": args.seed,
            "model": args.model,
            "judge_model": args.judge_model,
        },
        "summary": summary,
        "records": records,
    }
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {results_path}")


if __name__ == "__main__":
    asyncio.run(main())
