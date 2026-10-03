# Running with a Cost Limit

One research report makes many LLM calls: planning, sub-queries researched in parallel, summaries, and the final write-up. How many depends on the query, so the cost of a single report isn't fixed. This page shows one way to put a hard dollar limit on each research run without changing GPT Researcher's code, using [Inferrail](https://github.com/domondi1/inferrail), an open-source (Apache-2.0) OpenAI-compatible gateway.

Every LLM call carries the run's id and budget as two request headers. The gateway reserves each call's worst-case cost before forwarding it to OpenAI, so sub-queries running at the same time can't all spend the same remaining money, and a call that doesn't fit is refused (HTTP 402) before it reaches the provider. Afterwards you can see what the run cost.

## 1. Start the gateway

```bash
pip install inferrail
export OPENAI_API_KEY=sk-...
inferrail serve --quickstart --app-mode   # OpenAI-compatible endpoint on http://127.0.0.1:8000/v1
```

## 2. Point GPT Researcher at it

Budgets need a price for the model. Inferrail ships prices for models such as `gpt-5`, `gpt-5-mini` and `gpt-4o-mini` (`inferrail models` lists them). For a model it doesn't price, such as the default `gpt-5.4` family, either pick a priced model as below or add the price to the gateway's config; otherwise budgeted calls to that model are refused rather than guessed.

```bash
OPENAI_BASE_URL="http://127.0.0.1:8000/v1"
FAST_LLM="openai:gpt-5-mini"
SMART_LLM="openai:gpt-5"
STRATEGIC_LLM="openai:gpt-5"

# Embeddings go straight to OpenAI (the gateway handles chat completions only)
EMBEDDING_KWARGS='{"openai_api_base": "https://api.openai.com/v1"}'

# This run's id and dollar budget, sent on every LLM call
LLM_KWARGS='{"default_headers": {"X-Inferrail-Attribute-Work-Id": "report-001", "X-Inferrail-Budget-Usd": "0.50"}}'
```

`LLM_KWARGS` is passed to the chat model as-is, so `default_headers` goes out on every call. Use a new run id for each report: the budget is created the first time an id is seen and can't be raised afterwards.

## Several runs from Python

`LLM_KWARGS` in the environment applies to the whole process. To give each report its own budget, put it in a per-run config file instead (and leave `LLM_KWARGS` unset in the environment, since environment values take precedence):

```python
import json
from gpt_researcher import GPTResearcher

def researcher_for_run(query: str, run_id: str, budget_usd: str) -> GPTResearcher:
    path = f"/tmp/{run_id}.json"
    with open(path, "w") as f:
        json.dump({"LLM_KWARGS": {"default_headers": {
            "X-Inferrail-Attribute-Work-Id": run_id,
            "X-Inferrail-Budget-Usd": budget_usd,
        }}}, f)
    return GPTResearcher(query=query, report_type="research_report", config_path=path)
```

## When the budget runs out

The refused call fails with a 402. GPT Researcher retries a failed LLM call (up to 10 attempts with backoff) and then raises; the retries are refused by the gateway too, so they cost nothing, but the run takes a little while to fail. To see what a run cost:

```bash
inferrail work report-001
```

It shows the run's calls and total cost. The gateway stores counts and costs, not prompts or responses.

## Scope

This uses GPT Researcher's existing `OPENAI_BASE_URL`, `LLM_KWARGS` and `EMBEDDING_KWARGS` settings with the `openai` provider. The budget enforcement itself (reservation before the provider, refusal with 402, headers not forwarded upstream) has been tested with LangChain's `ChatOpenAI`, which is what GPT Researcher uses for OpenAI. Only calls that go through the gateway count, so retrievers and embeddings aren't included in the budget. Full setup and limitations: [Inferrail run-budget guide](https://tryinferrail.com/recipes/agent-run-budget.html?ref=gpt-researcher-docs).

*Disclosure: this page was contributed by the maintainer of Inferrail.*
