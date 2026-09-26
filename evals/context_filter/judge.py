"""Step 3: score the replayed reports and summarise.

Quality signals, from most to least objective:

  accuracy    SimpleQA questions have a known answer; each report is graded
              with the repo's SimpleQA grader (CORRECT / INCORRECT /
              NOT_ATTEMPTED).
  precision   Share of the context's chunks an independent judge model rates
              relevant to the research question. Measures the filter itself.
              Not defined for ``none``, which applies no filter.
  pairwise    Blind head-to-head against ``embeddings``, run in both orders
              to cancel position bias; a pair counts as a win only if the
              strategy wins both orders.

    python -m evals.context_filter.judge --results results/ --judge-model gpt-5.4
    python -m evals.context_filter.judge --results results/ --baseline none --only jev jev_wide
"""

import argparse
import asyncio
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

from openai import AsyncOpenAI

from evals.simple_evals.simpleqa_eval import GRADER_TEMPLATE

client = AsyncOpenAI()
SEM = asyncio.Semaphore(8)


async def ask(model: str, prompt: str) -> str:
    async with SEM:
        response = await client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content.strip()


async def grade_simpleqa(model: str, r: dict) -> str:
    text = await ask(model, GRADER_TEMPLATE.format(
        question=r["query"], target=r["answer"], predicted_answer=r["report"] or "(no report)"))
    return {"A": "CORRECT", "B": "INCORRECT", "C": "NOT_ATTEMPTED"}.get(text[:1], "NOT_ATTEMPTED")


def split_chunks(context: str) -> list[str]:
    return [c.strip() for c in re.split(r"\n(?=Source: )", "\n" + context) if c.strip()]


async def context_precision(model: str, r: dict) -> float | None:
    if r["strategy"] == "none":
        return None
    chunks = split_chunks(r["context"])
    if not chunks:
        return 0.0
    listing = "\n\n".join(f"[{i}] {c[:1500]}" for i, c in enumerate(chunks))
    text = await ask(model, (
        f"Research question: {r['query']}\n\n"
        f"Below are {len(chunks)} numbered passages. A passage is RELEVANT if it contains information "
        "that would help write an accurate answer to the research question; passages that are only "
        "on the same general topic, navigation, boilerplate or unrelated are NOT relevant.\n\n"
        f"{listing}\n\nReply with only a JSON list of the numbers of the RELEVANT passages, e.g. [0, 3]."))
    try:
        relevant = {int(i) for i in json.loads(re.search(r"\[.*?\]", text, re.S).group(0))}
    except (AttributeError, ValueError):
        return None
    return len(relevant & set(range(len(chunks)))) / len(chunks)


PAIRWISE = """You are comparing two research reports that answer the same question.

Question: {query}

=== Report 1 ===
{a}

=== Report 2 ===
{b}

Judge which report better answers the question: factual accuracy and specificity first, then
relevance (no padding or off-topic material), then completeness. Length alone is not a merit.
Reply with exactly one of: "1", "2", or "tie"."""


async def pairwise(model: str, r: dict, base: dict) -> str:
    """'win', 'loss' or 'tie' for r against base, requiring agreement across both orders."""
    first = await ask(model, PAIRWISE.format(query=r["query"], a=r["report"], b=base["report"]))
    second = await ask(model, PAIRWISE.format(query=r["query"], a=base["report"], b=r["report"]))
    first, second = first.strip('"').lower(), second.strip('"').lower()
    if first.startswith("1") and second.startswith("2"):
        return "win"
    if first.startswith("2") and second.startswith("1"):
        return "loss"
    return "tie"


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--judge-model", default="gpt-5.4")
    parser.add_argument("--precision-model", default="gpt-5.4-mini")
    parser.add_argument("--baseline", default="embeddings", help="strategy the pairwise judge compares against")
    parser.add_argument("--only", nargs="*", help="score only these strategies (the baseline is still loaded)")
    args = parser.parse_args()
    BASELINE = args.baseline

    by_strategy = defaultdict(dict)
    for path in args.results.glob("*/*.json"):
        r = json.loads(path.read_text())
        by_strategy[r["strategy"]][r["id"]] = r
    strategies = sorted(by_strategy, key=lambda s: (s != BASELINE, s))
    if args.only:
        strategies = [s for s in strategies if s in args.only]
    tag = f"_vs_{BASELINE}" + (f"_{'_'.join(args.only)}" if args.only else "")

    async def score(r: dict) -> dict:
        tasks = {"precision": context_precision(args.precision_model, r)}
        if r["kind"] == "simpleqa":
            tasks["grade"] = grade_simpleqa(args.judge_model, r)
        base = by_strategy[BASELINE].get(r["id"])
        if r["strategy"] != BASELINE and base and r["report"] and base["report"]:
            tasks["pairwise"] = pairwise(args.judge_model, r, base)
        values = await asyncio.gather(*tasks.values())
        return {**r, **dict(zip(tasks, values))}

    scored = await asyncio.gather(*[score(r) for s in strategies for r in by_strategy[s].values()])
    (args.results / f"scored{tag}.json").write_text(json.dumps(
        [{k: v for k, v in r.items() if k not in ("report", "context")} for r in scored], indent=1))

    rows = []
    for s in strategies:
        rs = [r for r in scored if r["strategy"] == s]
        sqa = [r for r in rs if r["kind"] == "simpleqa"]
        pw = [r["pairwise"] for r in rs if r.get("pairwise")]
        prec = [r["precision"] for r in rs if r.get("precision") is not None]
        med = lambda k: statistics.median(r[k] for r in rs)
        rows.append({
            "strategy": s,
            "runs": len(rs),
            "errors": sum(1 for r in rs if r["error"]),
            "simpleqa_correct": sum(r["grade"] == "CORRECT" for r in sqa),
            "simpleqa_incorrect": sum(r["grade"] == "INCORRECT" for r in sqa),
            "simpleqa_not_attempted": sum(r["grade"] == "NOT_ATTEMPTED" for r in sqa),
            "simpleqa_n": len(sqa),
            "precision": round(statistics.mean(prec), 3) if prec else None,
            f"pairwise_vs_{BASELINE}": {k: pw.count(k) for k in ("win", "tie", "loss")} if pw else None,
            "median_filter_seconds": med("filter_seconds"),
            "median_context_tokens": med("context_tokens"),
            "median_write_seconds": med("write_seconds"),
            "mean_filter_cost": round(statistics.mean(r["filter_cost"] for r in rs), 5),
            "mean_write_cost": round(statistics.mean(r["write_cost"] for r in rs), 4),
        })
    (args.results / f"summary{tag}.json").write_text(json.dumps(rows, indent=1))
    print(json.dumps(rows, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
