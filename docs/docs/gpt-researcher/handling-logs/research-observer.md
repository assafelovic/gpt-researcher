# Research lifecycle observer

Library users can pass an optional observer to `GPTResearcher` to receive
structured events while sources move through planning, search, and scraping.
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

Event payloads do not contain fetched page bodies, snippets, headers, cookies,
or credentials. Query and URL fields can contain user or source information;
observers that export or persist events are responsible for applying their own
access control, redaction, and retention policy.

Adding an observer does not add searches, fetches, model calls, retries, or
filtering decisions. Omitting it preserves the existing research behavior.
