"""Step 2: rebuild each run's context with every strategy, then write the report.

Strategies (all see the same recorded pages):

  embeddings  today's pipeline: 1000-char chunks, cosine similarity, top 10
  jev         same chunks, scored by Jev on a usefulness rubric, top 10
              of those scoring at least JEV_MIN_SCORE (default 1.5)
  jev_top10   Jev's 10 best chunks with no score threshold: the same budget
              as embeddings, isolating selection quality from context size
  jev_large   Jev on 3000-char chunks, top 4: a similar character budget
              with a third of the API calls (latency tuning; opt-in)
  jev_wide    Jev with the same threshold but up to 30 chunks: spends the
              precision on a larger budget when enough relevant chunks exist
  jev_broad   Jev on 3000-char chunks, looser threshold (1.0), up to 12:
              a larger budget for broad questions, still ranked
  bm25        keyword (BM25) ranking of the same chunks, top 10; no API, no
              model, no embeddings
  bm25_rel    BM25, keeping chunks scoring >= 50% of the best one, top 10
  bm25_wide   BM25 with the same relative threshold, up to 25 chunks
  none_capped no ranking: pages in search order, capped at ~12k tokens
              (48k chars) per sub-query
  none        no filtering: every page, in full, goes to the writer
  truncate    control: the same 10-chunk budget, taken round-robin across
              pages with no relevance ranking at all

``truncate`` answers whether ranking matters at all at this budget.
``none`` tests the "long context makes filtering unnecessary" hypothesis.

    python -m evals.context_filter.replay --runs runs/ --out results/
"""

import argparse
import asyncio
import json
import time
from pathlib import Path

import tiktoken
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from gpt_researcher import GPTResearcher
from gpt_researcher.context.compression import ContextCompressor
from gpt_researcher.context.jev_filter import JevContextCompressor
from gpt_researcher.context.lexical import LexicalContextCompressor
from gpt_researcher.context.retriever import SearchAPIRetriever
from gpt_researcher.prompts import PromptFamily

STRATEGIES = ["embeddings", "jev", "jev_top10", "none", "truncate"]
MAX_RESULTS = 10  # what ContextManager.get_similar_content_by_query uses
ENC = tiktoken.get_encoding("o200k_base")


def _pages_as_docs(pages: list[dict]) -> list[Document]:
    return SearchAPIRetriever(pages=pages).invoke("")


def _round_robin_chunks(pages: list[dict], n: int) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    per_page = [splitter.split_documents([d]) for d in _pages_as_docs(pages)]
    picked, i = [], 0
    while len(picked) < n and any(i < len(chunks) for chunks in per_page):
        picked += [chunks[i] for chunks in per_page if i < len(chunks)]
        i += 1
    return picked[:n]


async def build_context(strategy: str, query: str, pages: list[dict], researcher: GPTResearcher) -> tuple[str, float]:
    """Context for one sub-query, plus the filter's own cost in USD."""
    costs = []
    if strategy == "embeddings":
        text = await ContextCompressor(
            documents=pages,
            embeddings=researcher.memory.get_embeddings(),
            similarity_threshold=researcher.cfg.similarity_threshold,
        ).async_get_context(query=query, max_results=MAX_RESULTS, cost_callback=costs.append)
    elif strategy == "jev":
        text = await JevContextCompressor(documents=pages).async_get_context(
            query=query, max_results=MAX_RESULTS, cost_callback=costs.append)
    elif strategy == "jev_top10":
        text = await JevContextCompressor(documents=pages, min_score=0).async_get_context(
            query=query, max_results=MAX_RESULTS, cost_callback=costs.append)
    elif strategy == "jev_large":
        text = await JevContextCompressor(documents=pages, chunk_size=3000).async_get_context(
            query=query, max_results=4, cost_callback=costs.append)
    elif strategy == "jev_wide":
        text = await JevContextCompressor(documents=pages).async_get_context(
            query=query, max_results=30, cost_callback=costs.append)
    elif strategy == "jev_broad":
        text = await JevContextCompressor(documents=pages, chunk_size=3000, min_score=1.0).async_get_context(
            query=query, max_results=12, cost_callback=costs.append)
    elif strategy == "bm25":
        text = await LexicalContextCompressor(documents=pages).async_get_context(query, MAX_RESULTS)
    elif strategy == "bm25_rel":
        text = await LexicalContextCompressor(documents=pages, relative_threshold=0.5).async_get_context(query, MAX_RESULTS)
    elif strategy == "bm25_wide":
        text = await LexicalContextCompressor(documents=pages, relative_threshold=0.5).async_get_context(query, 25)
    elif strategy == "none_capped":
        docs, budget = [], 48_000
        for d in _pages_as_docs(pages):
            if budget <= 0:
                break
            docs.append(Document(page_content=d.page_content[:budget], metadata=d.metadata))
            budget -= len(docs[-1].page_content)
        text = PromptFamily.pretty_print_docs(docs)
    elif strategy == "none":
        text = PromptFamily.pretty_print_docs(_pages_as_docs(pages))
    elif strategy == "truncate":
        text = PromptFamily.pretty_print_docs(_round_robin_chunks(pages, MAX_RESULTS))
    else:
        raise ValueError(strategy)
    return text, sum(costs)


async def replay_one(run: dict, strategy: str, out: Path) -> None:
    path = out / strategy / f"{run['id']}.json"
    if path.exists():
        return
    researcher = GPTResearcher(query=run["query"], report_type="research_report")

    start = time.perf_counter()
    built = await asyncio.gather(*[
        build_context(strategy, call["query"], call["pages"], researcher) for call in run["calls"]
    ])
    filter_seconds = time.perf_counter() - start
    context = " ".join(text for text, _ in built if text)
    filter_cost = sum(cost for _, cost in built)

    start = time.perf_counter()
    try:
        report = await researcher.write_report(ext_context=context)
        error = None
    except Exception as e:  # e.g. the "none" context overflowing the model window
        report, error = "", f"{type(e).__name__}: {e}"
    write_seconds = time.perf_counter() - start

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "id": run["id"], "kind": run["kind"], "query": run["query"], "answer": run.get("answer"),
        "strategy": strategy,
        "filter_seconds": round(filter_seconds, 2),
        "filter_cost": filter_cost,
        "context_chars": len(context),
        "context_tokens": len(ENC.encode(context, disallowed_special=())),
        "write_seconds": round(write_seconds, 2),
        "write_cost": researcher.get_costs(),
        "report": report,
        "error": error,
        "context": context,
    }))
    print(f"{strategy:10} {run['id']}: filter {filter_seconds:5.1f}s ${filter_cost:.5f} | "
          f"ctx {len(context):>7} chars | write {write_seconds:5.1f}s ${researcher.get_costs():.4f}"
          + (f" | ERROR {error[:80]}" if error else ""), flush=True)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--strategies", nargs="+", default=STRATEGIES)
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()

    runs = [json.loads(p.read_text()) for p in sorted(args.runs.glob("*.json"))]
    sem = asyncio.Semaphore(args.concurrency)

    async def guarded(run, strategy):
        async with sem:
            await replay_one(run, strategy, args.out)

    await asyncio.gather(*[guarded(r, s) for r in runs for s in args.strategies if r["calls"]])


if __name__ == "__main__":
    asyncio.run(main())
