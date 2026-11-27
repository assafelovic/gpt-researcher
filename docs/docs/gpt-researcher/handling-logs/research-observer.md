# Research lifecycle observer

Library users can pass an optional observer to `GPTResearcher` to receive
structured events while sources move through planning, search, scraping, and
context selection.
The observer is disabled by default and does not replace the existing log or
WebSocket interfaces.

```python
from gpt_researcher import GPTResearcher


def observe(event, **fields):
    print(event, fields)


researcher = GPTResearcher(
    query="What changed in the latest release?",
    research_observer=observe,
)
```

An object with an `on_event(event, **fields)` method can be used instead. Both
synchronous and asynchronous handlers are supported. Observer exceptions are
suppressed so telemetry cannot interrupt or change a research run.

## Events

| Event | Fields | Meaning |
| --- | --- | --- |
| `query_planned` | `query`, `position` | A planned query will be researched. |
| `candidate_discovered` | `query`, `provider`, `url`, `rank` | A search provider returned a candidate. |
| `search_empty` | `query`, `provider` | A provider returned no candidates. |
| `search_failed` | `query`, `provider`, `reason_code` | A provider failed and research continued, or an initial planning search failed before being re-raised. |
| `selected_for_fetch` | `query`, `url` | A candidate passed URL deduplication. |
| `candidate_deduplicated` | `query`, `url`, `reason_code` | A previously visited URL was not fetched again. |
| `content_prefetched` | `query`, `provider`, `url`, `rank`, `content_length` | A provider supplied content that did not require scraping. |
| `fetch_succeeded` | `url`, `scraper`, `content_length` | A scraper produced a retained row. |
| `fetch_failed` | `url`, `scraper`, `content_length`, `reason_code` | A scraper failure was observed before the row was discarded. |
| `context_selected` | `query`, `filter`, `filter_used`, `fallback_reason`, `candidate_pages`, `candidate_chunks`, `context_chars`, `selected` | The context filter chose what a research query's context is built from. |

### `context_selected`

One event each time research selects context from fetched pages (normally
once per sub-query, plus user-supplied source URLs and initial search results),
emitted after the context string is built:

- `filter`: the `CONTEXT_FILTER` setting as configured (`auto` when unset).
- `filter_used`: what actually chose the context: `jev`, `keyword`,
  `embeddings`, `none` (every page in full), or `shortcut` (the input was below
  `COMPRESSION_THRESHOLD`, so every page was kept in full without filtering).
- `fallback_reason`: the exception type name (for example `JevError`) when the
  requested filter failed and keyword ranking ran instead; otherwise `null`.
- `candidate_pages`: pages offered to the filter.
- `candidate_chunks`: chunks the filter ranked (`keyword` and `jev`); `null`
  when not chunked or not exposed (`embeddings`).
- `context_chars`: length of the resulting context string.
- `selected`: the chunks in the context, in context order, each
  `{url, rank, start, length, score}`. `rank` starts at 1. `start` and `length`
  are character offsets into the page text as the filter saw it (truncated to
  `MAX_CONTENT_CHARS`, 50,000 by default), so `text[start:start + length]` is
  the chunk; `start` is `null` if the offset could not be determined. `score`
  is the BM25 score (`keyword`), Jev usefulness 0-3 (`jev`), cosine similarity
  (`embeddings`), or `null` for whole pages.

Event payloads do not contain fetched page bodies, snippets, headers, cookies,
or credentials. Query and URL fields can contain user or source information;
observers that export or persist events are responsible for applying their own
access control, redaction, and retention policy.

Adding an observer does not add searches, fetches, model calls, retries, or
filtering decisions. Omitting it preserves the existing research behavior.
