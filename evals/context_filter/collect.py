"""Step 1: run each query once and record what reached the context filter.

Every scraped page reaches the report through
``ContextManager.get_similar_content_by_query(query, pages)``. This records
each call's inputs, so ``replay.py`` can rebuild the context from the exact
same pages with every strategy. Only the filter varies; search results and
scraping, the noisiest parts of a run, are held fixed.

    python -m evals.context_filter.collect --out runs/ --concurrency 4
"""

import argparse
import asyncio
import json
import time
from pathlib import Path

from gpt_researcher import GPTResearcher
from gpt_researcher.skills.context_manager import ContextManager

HERE = Path(__file__).parent

# researcher -> recorded calls. Patched once for the whole process, because
# runs execute concurrently and per-run patch/restore would race.
_RECORDINGS: dict[int, list] = {}
_original = ContextManager.get_similar_content_by_query


async def _recording(self, query, pages):
    calls = _RECORDINGS.get(id(self.researcher))
    if calls is not None:
        calls.append({"query": query, "pages": [
            {"url": p.get("url"), "title": p.get("title"), "raw_content": p.get("raw_content")}
            for p in pages
        ]})
    return await _original(self, query, pages)


ContextManager.get_similar_content_by_query = _recording


async def collect_one(item: dict, out: Path, sem: asyncio.Semaphore) -> None:
    path = out / f"{item['id']}.json"
    if path.exists():
        return
    async with sem:
        researcher = GPTResearcher(query=item["query"], report_type="research_report")
        calls = _RECORDINGS[id(researcher)] = []
        start = time.perf_counter()
        try:
            await researcher.conduct_research()
        except Exception as e:
            print(f"{item['id']}: FAILED {e}")
            return
        finally:
            _RECORDINGS.pop(id(researcher), None)
        path.write_text(json.dumps({
            **item,
            "research_seconds": round(time.perf_counter() - start, 1),
            "research_cost": researcher.get_costs(),
            "calls": calls,
        }))
        print(f"{item['id']}: {len(calls)} filter calls, "
              f"{sum(len(c['pages']) for c in calls)} pages, {time.perf_counter() - start:.0f}s", flush=True)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE / "runs")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    items = json.loads((HERE / "queries.json").read_text())
    sem = asyncio.Semaphore(args.concurrency)
    await asyncio.gather(*[collect_one(item, args.out, sem) for item in items])


if __name__ == "__main__":
    asyncio.run(main())
