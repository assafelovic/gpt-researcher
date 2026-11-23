# Costs

GPT Researcher tracks the LLM cost of every run. This page shows what a run costs with the default settings, where that money goes, and how to make it cheaper.

## What a research run costs

Measured on November 22–23, 2026 with the default configuration:

| Report type | LLM cost | Time | Sources read | Searches | Report length |
|---|---|---|---|---|---|
| Research report (`research_report`) | \$0.08 (\$0.066–\$0.098) | about a minute | 12–19 | 5 | ~2,000 words |
| Detailed report (`detailed_report`) | \$0.34 (\$0.29–\$0.39) | 2–2.5 minutes | 52–68 | 17 | 5,200–6,000 words |
| [Deep research](/docs/gpt-researcher/gptr/deep_research) (`deep`) | \$1.30 (\$1.14–\$1.41) | 7–12 minutes | 124–146 | ~46 | ~2,300 words |

The research report figures are from 11 runs, the detailed report from 2 and deep research from 4, across topics in finance, medicine, energy, software and astronomy. The configuration was:

- `FAST_LLM=openai:gpt-5.4-mini`, `STRATEGIC_LLM=openai:gpt-5.4`, `SMART_LLM=openai:gpt-6-sol`
- `RETRIEVER=tavily` (basic search)
- `CONTEXT_FILTER=auto` without a `TYPESAFE_API_KEY`, so the free keyword filter
- Everything else at its default, including `DEEP_RESEARCH_BREADTH=3` and `DEEP_RESEARCH_DEPTH=2`

Your costs will vary with the topic, the models and your settings. To see the exact cost of your own runs, use [`get_costs()`](#tracking-costs).

## Search costs

The LLM costs above don't include your search API. Tavily, the default retriever, charges 1 credit per basic search. Its free plan includes 1,000 credits a month, and pay-as-you-go is \$0.008 per credit (see [Tavily credits and pricing](https://docs.tavily.com/documentation/api-credits)).

| Report type | Searches | Pay-as-you-go cost |
|---|---|---|
| Research report | 5 | ~\$0.04 |
| Detailed report | 17 | ~\$0.14 |
| Deep research | ~46 | ~\$0.37 |

On the free plan that's about 200 research reports, 55 detailed reports or 20 deep research runs a month. Other [retrievers](/docs/gpt-researcher/search-engines) have their own pricing; DuckDuckGo and a self-hosted SearX are free.

## Where the money goes

`get_step_costs()` splits a run's cost by step. Averaged over three research reports with the default models:

| Step | What happens | Cost | Share |
|---|---|---|---|
| `agent_selection` | Picks the research agent and its instructions | \$0.002 | 3% |
| `research` | Plans sub-queries, searches, scrapes and filters context | \$0.007 | 8% |
| `report_writing` | `SMART_LLM` reads the filtered context and writes the report | \$0.073 | 89% |

Writing the report is almost the whole bill, so `SMART_LLM` is the setting that matters most for cost.

Deep research is the other way around. In a measured \$1.36 run, the recursive research phase (`deep_research`) cost \$1.25 and writing the final report \$0.11. By model, `STRATEGIC_LLM` (`gpt-5.4`), which plans each branch and digests what it finds, accounted for \$1.22 of the total. So for deep research, `STRATEGIC_LLM`, breadth and depth are the settings that matter most.

`FAST_LLM` is only used to plan images when [image generation](/docs/gpt-researcher/gptr/image_generation) is on, so it doesn't affect the cost of a normal run.

## Making runs cheaper

**Use a cheaper writing model.** With `FAST_LLM=openai:gpt-5.4-nano`, `STRATEGIC_LLM=openai:gpt-5.4-mini` and `SMART_LLM=openai:gpt-5.4-mini`, three research reports averaged \$0.056 (\$0.052–\$0.063), about 30% less than the defaults, in about the same time. Reports were 1,360–2,020 words. Setting all three to `openai:gpt-5.4-mini` gave about the same result (\$0.057 on average). The [model table](/docs/gpt-researcher/gptr/config#choosing-an-llm) ranks models by how faithfully they stick to their sources, which is worth checking before you switch.

**Keep the context filter on.** The filter (on by default) decides which scraped passages reach the writer. Turning it off with `CONTEXT_FILTER=none` cost 65% more per report in our [context filter benchmark](/docs/gpt-researcher/gptr/context-filter). With a `TYPESAFE_API_KEY`, the default Jev filter adds about half a cent per report.

**Ask for less.** `TOTAL_WORDS` sets the target report length, and `MAX_SEARCH_RESULTS_PER_QUERY` sets how many results each search returns. For deep research, `DEEP_RESEARCH_BREADTH` and `DEEP_RESEARCH_DEPTH` control how many branches it explores, and each branch is a full research pass. See [configuration](/docs/gpt-researcher/gptr/config).

**Run models locally.** With [Ollama](/docs/gpt-researcher/llms/running-with-ollama) there is no LLM bill at all, only your search API.

## Tracking costs

Every run adds up its own spend:

```python
from gpt_researcher import GPTResearcher

researcher = GPTResearcher(query="Are solid-state batteries ready for EVs?", report_type="research_report")
await researcher.conduct_research()
report = await researcher.write_report()

print(researcher.get_costs())       # total in USD, e.g. 0.0781
print(researcher.get_step_costs())  # {'agent_selection': 0.0019, 'research': 0.0062, 'report_writing': 0.0717}
```

The REST API returns the same total: `POST /report/` includes it as `research_information.research_costs`.

If you pass a `log_handler` to `GPTResearcher`, its async `on_research_step(step, details)` method receives a `cost_update` event after every billed call, with `cost` (that call), `total_cost` (the run so far) and `step_name` in `details`.

## How costs are calculated

- **From real token usage.** Each LLM call's cost comes from the token counts the provider returns, multiplied by that model's price. Prices for OpenAI and Anthropic models live in [`gpt_researcher/utils/costs.py`](https://github.com/assafelovic/gpt-researcher/blob/main/gpt_researcher/utils/costs.py) and are current as of November 2026.
- **Prompt caching is discounted.** Cached OpenAI input tokens are billed at half price. Anthropic cache reads are billed at 0.1× the input price and cache writes at 1.25×.
- **Other models are estimated.** For models not in the price table, including Gemini, OpenRouter and local models, GPT Researcher assumes \$5 per million input tokens and \$15 per million output tokens. Treat `get_costs()` as a rough estimate for those, and as zero for local models.
- **Embeddings** are estimated at \$0.02 per million tokens, the price of `text-embedding-3-small`. They're only billed when `CONTEXT_FILTER=embeddings`.
- **Not included:** search API credits, paid scraping services, and the images themselves when [image generation](/docs/gpt-researcher/gptr/image_generation) is on (the LLM call that plans them is included).
