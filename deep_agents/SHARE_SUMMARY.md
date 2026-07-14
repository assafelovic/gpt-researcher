# GPT Researcher x Deep Agents: 2x the verified evidence, same harness

*A shareable summary of the new Deep Agents example and its benchmark results.
Full details: [example](https://github.com/assafelovic/gpt-researcher/tree/master/deep_agents),
[BENCHMARK.md](https://github.com/assafelovic/gpt-researcher/blob/master/deep_agents/BENCHMARK.md).*

## What we built

We plugged GPT Researcher into LangChain's
[Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) as
the research engine: a chief-editor deep agent plans a report outline with
`write_todos`, spawns parallel `researcher` subagents, and each subagent
calls GPT Researcher's full pipeline (`deep_research`) to produce a cited
section draft. The harness handles orchestration; GPT Researcher handles
evidence. It reproduces the STORM-style pipeline of our 8-agent LangGraph
example in a fraction of the code, and works over the web, local documents
(PDF/DOCX/md), or both.

## What we measured

The obvious question: does swapping the quickstart's raw search tool for
GPT Researcher actually make the agent's research better? We ran both on
[DeepResearch Bench](https://github.com/Ayanami0730/deep_research_bench)
(RACE report quality + FACT citation verification, 10 topic-stratified
tasks), keeping everything else identical - same `create_deep_agent`
harness, same `gpt-5.4` model, same system prompt, same step budget. The
only variable was the research tooling.

| Metric | Deep agent + raw Tavily search | Deep agent + GPT Researcher |
|---|---|---|
| RACE report quality | 0.503 | **0.512** |
| Citations per report | 34.5 | **62.9** |
| **Effective (verified) citations per report** | 18.6 | **35.2 (+89%)** |
| Citation precision | 53.9% | **56.0%** |
| Per-task wins (verified citations) | 3/10 | **7/10** |

Every citation was verified by the official FACT pipeline: extract the
claim, fetch the cited page, judge whether the page supports the claim.
So this isn't "more links" - it's **~2x the claims a reader can actually
verify**, at equal-or-better report quality and higher precision. For
calibration, 35 effective citations per report is in the range DeepResearch
Bench reports for dedicated deep research products (OpenAI Deep Research
~40), while plain LLM + search-tool setups typically land at 5-15.

## Accuracy and breadth, not just depth

- **No accuracy tax**: on quick single-fact lookups (SimpleQA, n=30) the
  two setups score at parity (83.3% vs 83.3%) - the heavier pipeline costs
  nothing on simple lookups.
- **Blind judge preference**: in a pairwise report comparison on 8 topics
  (sides randomized), an LLM judge preferred the GPT Researcher agent's
  report **5 of 8 times**, with more distinct sources cited (24.5 vs 19.5
  unique URLs) at comparable length.
- **Breadth beyond the web**: with GPT Researcher's `hybrid` mode, the same
  agent researches private documents alongside the web. On a due-diligence
  task over a realistic fictional internal corpus (27 files: PDFs, DOCX,
  distractors, stale archived vintages - no leakage from the public web
  possible), it recovered **up to 94% of internal-document facts vs 0%**
  for the raw-search agent. Even the DIY alternative - mounting the corpus
  on the deep agent's own file tools - averages only 62.5%: it has to
  guess which files to read, cannot parse DOCX, and sometimes trusts an
  archived vintage. GPT Researcher's format-aware parsing and embedding
  retrieval make it both higher and consistent, at equal public-web fact
  coverage.

## Why it works

A raw search tool returns snippets, so the writing model cites whatever the
search API surfaced and fills gaps from memory. GPT Researcher plans
sub-queries, scrapes and reads the full pages, filters content by relevance,
and hands the agent pre-cited synthesis - so what reaches the final report
is grounded in sources that were actually read.

## Reproduce it

Everything ships in the repo: the agent builders, a generation script that
emits DeepResearch Bench-format reports for both setups, and a small patch
adding an OpenAI judge backend to the official scoring harness. See
[BENCHMARK.md](https://github.com/assafelovic/gpt-researcher/blob/master/deep_agents/BENCHMARK.md)
for the three commands.
