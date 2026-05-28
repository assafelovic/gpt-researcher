# One-line summary

Track Anthropic costs from native usage metadata instead of relying on the fallback tiktoken estimator.

## Problem

Anthropic requests were being costed with a generic text-length estimator rather than the provider's native token usage metadata. That made Anthropic totals inaccurate, especially for streaming responses and tool-calling flows where usage arrives through response metadata rather than plain text length.

## Solution

- add Anthropic-specific pricing rules in `gpt_researcher/utils/costs.py`
- prefer `response_metadata["usage"]` / `usage_metadata` when Anthropic returns native token counts
- capture usage and response metadata in `GenericLLMProvider` for both normal and streaming responses
- use the same cost-calculation path in `create_chat_completion()` and tool-calling flows
- add focused tests for pricing and streaming metadata capture

## Testing

Verified locally with:

- `uv run python -c "import gpt_researcher; print('ok')"`
- `uv run python -m unittest tests.test_costs tests.test_llm_usage_tracking`

## Breaking changes

None.

## Related issues

None identified.
