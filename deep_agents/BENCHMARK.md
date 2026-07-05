# Benchmark: GPT Researcher as a Deep Agent's Research Engine

Does giving a [deep agent](https://docs.langchain.com/oss/python/deepagents/overview)
GPT Researcher as its research engine actually produce better research than
the stock setup? We measured it on
[DeepResearch Bench](https://github.com/Ayanami0730/deep_research_bench), the
industry-standard benchmark for deep research agents (100 PhD-vetted research
tasks; we sampled 10 English tasks stratified across its topic domains).

## Setup

Two deep agents, identical in every way except the research tooling:

| | Baseline | GPT Researcher agent |
|---|---|---|
| Harness | `deepagents` `create_deep_agent` | same |
| Model | `gpt-5.4` | same |
| System prompt | shared report-writing prompt | same |
| Step budget | recursion limit 60 | same |
| Research tools | raw Tavily `internet_search` (the [deepagents quickstart](https://docs.langchain.com/oss/python/deepagents/quickstart) setup) | GPT Researcher `quick_search` + `deep_research` |

Both agents were asked to produce fully cited markdown research reports.
Scoring used the official DeepResearch Bench pipeline:

- **RACE** - report quality (comprehensiveness, insight, instruction
  following, readability), judged blind by GPT-5.5 against reference reports.
- **FACT** - citation grounding: every cited claim is extracted, the cited
  page is fetched, and a judge verifies whether the page actually supports
  the claim. "Effective citations" = verified supported citations per report.

## Results

| Metric | Baseline (Tavily) | GPT Researcher agent | Δ |
|---|---|---|---|
| RACE overall | 0.503 | **0.512** | +1.9% |
| Citations per report | 34.5 | **62.9** | +82% |
| **Effective (verified) citations per report** | 18.6 | **35.2** | **+89%** |
| Citation precision | 53.9% | **56.0%** | +2.1pts |
| Per-task wins (effective citations) | 3 | **7** | |

The headline: at the same model, prompt and step budget, the GPT Researcher
agent grounds its reports in **~2x the verified evidence** of the stock
deep-agent setup, with report quality (RACE) also ahead on every dimension.
For calibration against the published DeepResearch Bench leaderboard, 35
effective citations per report is in the range of dedicated deep research
products (OpenAI Deep Research ~40, plain LLMs with search tools ~5-15).

Why: a raw search tool returns snippets, so the writing model cites whatever
the search API surfaced. GPT Researcher's pipeline plans sub-queries, scrapes
and reads the actual pages, filters content by relevance against the query,
and returns pre-cited synthesis - so far more of what reaches the final
report is real, verifiable sourcing.

The gains compound with GPT Researcher core improvements
([#1861](https://github.com/assafelovic/gpt-researcher/pull/1861): smarter
Tavily `site:` handling, scrapers that reject error pages and retry transient
failures, stricter relevance filtering, stronger citation grounding in
prompts): before those fixes the same agent scored 25.8 effective citations
(+39% over baseline); after them, 35.2 (+89%).

## Reproducing

1. Clone the benchmark harness, apply the small patch from this directory
   (adds an OpenAI judge backend alongside the stock Gemini one, plus a
   keyless Jina fallback for citation scraping), and install its requirements:

   ```bash
   git clone https://github.com/Ayanami0730/deep_research_bench /tmp/deep_research_bench
   git -C /tmp/deep_research_bench apply "$(pwd)/deep_agents/drb_harness.patch"
   pip install -r /tmp/deep_research_bench/requirements.txt
   ```

2. Generate reports for both agents (from the gpt-researcher repo root;
   needs `OPENAI_API_KEY` and `TAVILY_API_KEY`):

   ```bash
   pip install -r requirements.txt -r deep_agents/requirements.txt
   python deep_agents/drb_generate.py --bench-dir /tmp/deep_research_bench --num-tasks 10
   ```

   This samples the same seeded, topic-stratified 10 English tasks and writes
   both agents' reports into the harness's `raw_data` folder in its expected
   format. Expect roughly 30-60 minutes and a few dollars of API usage per
   agent.

3. Score with the official pipeline (the patch defaults the judges to
   GPT-5.5 for RACE and GPT-5.4-mini for FACT):

   ```bash
   cd /tmp/deep_research_bench
   LLM_BACKEND=openai bash run_benchmark.sh
   ```

   (The patch already points `TARGET_MODELS` at both agents.)

   Results land in `results/race/<agent>/race_result.txt` and
   `results/fact/<agent>/fact_result.txt`.

Notes: FACT re-fetches every cited URL at scoring time, so sites that block
scrapers count against both agents equally. Scores on a 10-task sample have
meaningful variance; the RACE gap is small, while the effective-citation gap
is large and consistent (7/10 per-task wins).
