"""Generate reports for DeepResearch Bench (official harness) from both agents.

Samples English tasks from the official query set (stratified by topic, seeded)
and runs the two deep agents on the raw task prompts, saving outputs in the
benchmark's required raw_data JSONL format:
    {"id": ..., "prompt": ..., "article": ...}

Usage (from the repository root):
    python deep_agents/drb_generate.py --bench-dir /tmp/deep_research_bench --num-tasks 10
"""

from dotenv import load_dotenv
import argparse
import asyncio
import json
import os
import random
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

from datetime import datetime

from deep_agents.benchmark import build_baseline_agent, build_gptr_agent

# Report-writing prompt shared by both agents. DeepResearch Bench evaluates
# long-form research reports, and its FACT pipeline can only verify claims
# whose sources appear as URLs in the report body - so inline citations are a
# hard requirement, exactly as for the products on the DRB leaderboard.
REPORT_SYSTEM_PROMPT = f"""You are an expert research analyst. Today's date \
is {datetime.now().strftime('%B %d, %Y')}. Use your tools to research the \
user's request thoroughly, then write a comprehensive, in-depth research \
report that fully addresses it.

Requirements for the final report:
- It must be a complete, well-structured markdown report (headings, sections,
  and where useful tables) - not a chat reply or a summary of what you did.
- Ground every substantive claim in researched sources, not your own memory -
  your training data predates today.
- Cite sources inline throughout the body as markdown links, e.g.
  ([reuters.com](https://www.reuters.com/...)), immediately after the claims
  they support. Every section should carry citations; aim to cite every
  distinct source your research surfaced that you actually used. Do not
  invent URLs - only cite URLs that appeared in your research results.
- Be comprehensive: cover breadth (all angles of the request) and depth
  (specific figures, dates, names) rather than generic statements.

Your final message must be the report itself, nothing else."""

SYSTEMS = {
    "baseline-tavily-deepagent": build_baseline_agent,
    "gptr-deepagent": build_gptr_agent,
}


def sample_tasks(query_file: Path, num_tasks: int, seed: int) -> list[dict]:
    rows = [json.loads(line) for line in open(query_file, encoding="utf-8")]
    en = [r for r in rows if r["language"] == "en"]
    # Stratified: allocate slots proportionally to topic frequency, then fill
    rng = random.Random(seed)
    by_topic: dict[str, list] = {}
    for r in en:
        by_topic.setdefault(r["topic"], []).append(r)
    topics = sorted(by_topic, key=lambda t: -len(by_topic[t]))
    picked = []
    while len(picked) < num_tasks:
        for topic in topics:
            pool = [r for r in by_topic[topic] if r not in picked]
            if pool and len(picked) < num_tasks:
                picked.append(rng.choice(pool))
    return picked[:num_tasks]


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bench-dir", type=Path, default=Path("/tmp/deep_research_bench"))
    parser.add_argument("--num-tasks", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--model", type=str, default=os.environ.get("STRATEGIC_LLM", "openai:gpt-5.4"))
    args = parser.parse_args()

    tasks = sample_tasks(args.bench_dir / "data/prompt_data/query.jsonl", args.num_tasks, args.seed)
    print(f"Sampled {len(tasks)} EN tasks: {Counter(t['topic'] for t in tasks)}")
    print("ids:", [t["id"] for t in tasks])

    raw_dir = args.bench_dir / "data/test_data/raw_data"
    semaphore = asyncio.Semaphore(args.concurrency)

    for system, builder in SYSTEMS.items():
        agent, _ = builder(args.model, system_prompt=REPORT_SYSTEM_PROMPT)
        out_path = raw_dir / f"{system}.jsonl"
        done_ids = set()
        if out_path.exists():
            done_ids = {json.loads(l)["id"] for l in open(out_path, encoding="utf-8")}
            print(f"[{system}] resuming, {len(done_ids)} tasks already done")

        async def run_task(task: dict, agent=agent, system=system):
            async with semaphore:
                start = time.perf_counter()
                print(f"[{system}] task {task['id']} ({task['topic']}) writing...")
                try:
                    result = await asyncio.wait_for(
                        agent.ainvoke(
                            {"messages": [{"role": "user", "content": task["prompt"]}]},
                            config={"recursion_limit": 60},
                        ),
                        timeout=1800,
                    )
                    message = result["messages"][-1]
                    article = getattr(message, "text", "")
                    if callable(article):
                        article = article()
                except Exception as e:
                    print(f"[{system}] task {task['id']} FAILED: {type(e).__name__}: {e}")
                    article = ""
                print(f"[{system}] task {task['id']} done ({time.perf_counter()-start:.0f}s, {len((article or '').split())} words)")
                return {"id": task["id"], "prompt": task["prompt"], "article": article or ""}

        pending = [t for t in tasks if t["id"] not in done_ids]
        results = await asyncio.gather(*(run_task(t) for t in pending))
        with open(out_path, "a", encoding="utf-8") as f:
            for row in results:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"[{system}] wrote {len(results)} articles to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
