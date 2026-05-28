# One-line summary

Fix Brave search result classification so snippet-only results are sent to the scraper instead of being treated as already-fetched full content.

## Problem

Brave search results populate `body` with snippet text, not full-page content. In `ResearchConductor._search_relevant_source_urls()`, results were classified as already-fetched whenever `len(raw_content) > 100`, where `raw_content` fell back to `result["body"]`. That caused Brave results with long snippets to bypass scraping entirely.

In the failing reproduction, this manifested as every sub-query logging **"Scraping content from 0 URLs"** because all Brave hits were treated as prefetched content before the scraper ever saw them.

This PR intentionally contains only the snippet-classification fix. The separate scraped-count tracking used by local safeguard logic belongs to the safeguards PR, not this one.

## Solution

- Stop treating `body` as full page content in `_search_relevant_source_urls()`
- Use only explicit `raw_content` to identify retriever results that already contain full text
- Leave snippet-only results in the URL list so the normal scraper path runs
- Add focused tests covering:
  - snippet-only retriever results are queued for scraping
  - explicit `raw_content` results remain prefetched

## Testing

Verified locally with:

- `uv run python -c "from gpt_researcher.skills.researcher import ResearchConductor; print('ok')"`
- `uv run python -m unittest tests.test_research_conductor_retrieval`

## Breaking changes

None.

## Related issues

- Potentially related: #1263
