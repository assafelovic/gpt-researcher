# One-line summary

Add fail-fast retrieval and budget safeguards, richer run metadata, and a stronger multi-probe retriever preflight.

## Problem

The CLI could start expensive research runs without proving that retrieval was healthy, and it would continue through repeated empty web-retrieval steps. Budget enforcement also missed deep-research child work because nested researchers did not share the same budget accumulator. Run artifacts also lacked enough metadata to diagnose failures after the fact.

Companion PR: `pr/fix-deep-research-abort-propagation` depends on this one.

## Solution

- introduce `RetrievalFailureError` and abort after repeated empty retrieval steps
- make `_scrape_data_by_urls()` report actual usable scraped entries so the safeguard counts real content, not just discovered URLs
- add CLI retriever preflight checks before LLM work starts
- persist run metadata in markdown frontmatter and sidecar `.meta.json` outputs
- add `MAX_COST_USD` enforcement and make deep-research child researchers share the parent budget state
- refine preflight to use three probe queries with delays and optional rate-limit logging when a retriever exposes that metadata
- add safeguard-focused tests for preflight and deep-research budget propagation

## Testing

Verified locally with:

- `uv run python -c "import gpt_researcher; print('ok')"`
- `uv run python -m unittest tests.test_cli_preflight tests.test_budget_cap_binding`

## Breaking changes

None.

## Related issues

None identified.
