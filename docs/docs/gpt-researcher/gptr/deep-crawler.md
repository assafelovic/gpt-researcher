# Bounded Deep Crawler

GPT Researcher in this fork does not rely on a free-form, unbounded crawl. Instead, it uses a bounded discovery layer that ranks search hits, follows a small number of relevant links, and hands the resulting URL set to the existing scraper pipeline.

The goal is simple: improve source coverage and source quality without turning research into a noisy spider.

## What It Does

- Scores search results before scraping them
- Prefers same-domain and docs-style pages when they match the task
- Follows a limited number of links from promising pages
- Filters obvious noise such as login, signup, privacy, and other utility pages
- Deduplicates URLs before they reach the scraper
- Preserves the original order of the highest-ranked URLs

## How It Works

The discovery flow is implemented in:

- `gpt_researcher/actions/deep_crawler.py`
- `gpt_researcher/skills/researcher.py`

At a high level, the flow is:

1. Search retrievers return seed URLs.
2. Each candidate URL is scored with query overlap, domain preference, and docs/reference hints.
3. The top candidates are crawled one level deeper by extracting hyperlinks from the page HTML.
4. New links are scored again and filtered against the current query and domain constraints.
5. The final ranked list is passed to the scraper layer for normal content extraction.

This means the crawler is a discovery step, not a replacement for the scraper. It decides *what to fetch next*, while the existing scraper decides *how to extract the content*.

## Configuration

The crawler is enabled by default and can be tuned with these settings:

- `ENABLE_DEEP_CRAWLER`
- `DEEP_CRAWLER_DEPTH`
- `DEEP_CRAWLER_BREADTH`
- `DEEP_CRAWLER_CONCURRENCY`
- `DEEP_CRAWLER_MAX_PAGES`
- `DEEP_CRAWLER_MAX_LINKS_PER_PAGE`
- `DEEP_CRAWLER_ALLOW_EXTERNAL_LINKS`
- `DEEP_CRAWLER_TIMEOUT`

Recommended starting values for most research tasks:

- `DEEP_CRAWLER_DEPTH=1`
- `DEEP_CRAWLER_BREADTH=4`
- `DEEP_CRAWLER_MAX_PAGES=12`
- `DEEP_CRAWLER_ALLOW_EXTERNAL_LINKS=false`

## When It Helps

The bounded crawler is most useful for:

- API documentation
- SDK references
- product manuals
- developer guides
- knowledge-base articles

It is less useful for:

- broad news research
- highly heterogeneous search spaces
- tasks where every result is intentionally unrelated but still useful

## Validation

The crawler is covered by:

- `tests/test_deep_crawler.py`
- `tests/test_query_planner_hardening.py`

Those tests verify:

- docs pages outrank obvious noise pages
- same-domain links are discovered and retained
- the research conductor preserves the crawler's ordering

## Practical Effect

For a query like "FastAPI async API docs", the crawler will prefer official documentation paths and deprioritize pages like login or account flows. For a broader query, it still stays bounded and will not recursively fan out forever.
