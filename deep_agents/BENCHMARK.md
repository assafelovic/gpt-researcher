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

## Supporting results

**No accuracy tax on quick factual Q&A.** On
[SimpleQA](https://openai.com/index/introducing-simpleqa/) (30-question
sample, standard grader) the two setups are at parity: 83.3% vs 83.3%. That
is the expected result - a raw search snippet is enough to look up one
fact - and it means the heavier pipeline costs nothing on simple accuracy.
The gap opens when the task is actual research.

**Report head-to-head (n=8, LLM judge).** Before adopting DeepResearch
Bench we ran a blind pairwise comparison: both agents wrote reports on the
same 8 topics, and an LLM judge picked the better report of each pair
(sides randomized). The GPT Researcher agent won **overall on 5 of 8
topics**, with more distinct sources cited per report (24.5 vs 19.5 unique
URLs) at comparable length. This run predates the core improvements of
[#1861](https://github.com/assafelovic/gpt-researcher/pull/1861);
DeepResearch Bench above is the rigorous, post-fix version of the same
question. Reproduce with `python deep_agents/report_benchmark.py`.

**Breadth beyond the web: private documents.** GPT Researcher's `local` and
`hybrid` modes run the same pipeline over your own documents (`DOC_PATH`).
We measured this with a due-diligence task over a corpus of fictional
internal company documents (an invented robotics company, so no fact can
leak from the public web) combined with real market context, graded per
fact-checkpoint by an LLM judge against ground truth.

The corpus is shaped like a real document share: 27 files across department
folders, with the fact-bearing documents as PDF, DOCX and markdown,
surrounded by distractors (HR policies, IT runbooks, marketing notes) and
stale archived vintages of the same reports whose outdated numbers count as
wrong. Three arms: the raw-search baseline, the obvious DIY alternative
(stock deepagents with its `ls`/`read_file` tools mounted on the corpus),
and GPT Researcher in hybrid mode:

| Internal-fact coverage (avg of 3 runs) | |
|---|---|
| Deep agent + raw search | 0% |
| Deep agent + raw search + file tools on the corpus | 62.5% |
| Deep agent + GPT Researcher (hybrid) | **87.5% (up to 94%)** |

(Public-web fact coverage is equal across all three arms, ~40-46%.)

The web-only agent hallucinates or omits every internal fact. The DIY
file-tools agent does recover internal facts - on a trivial corpus of just
the four fact documents as markdown it even reaches parity - but on the
realistic corpus it turns erratic: it must guess which of 27 files to read
within its step budget, plain-text file reads cannot parse DOCX (it missed
or took stale values for the product-brief facts in every run), and it
sometimes trusts an archived vintage. GPT Researcher's document pipeline
(format-aware parsing, embedding-based retrieval over the whole corpus)
recovers up to 94% of the internal facts, at equal web coverage, in the
same run that researches the web. Reproduce with
`python deep_agents/hybrid_benchmark.py` (the corpus ships in
`benchmark_data/internal_docs/`, regenerable with
`benchmark_data/build_corpus.py`).

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

## Raw results

Following the repo's [`evals/`](../evals) convention, the run artifacts
behind every table above are tracked in `benchmark_results/`:

| Table | Artifact |
|---|---|
| DeepResearch Bench RACE + FACT | `benchmark_results/drb/<agent>_race_result.txt` and `<agent>_fact_result.txt` (official pipeline output) |
| Hybrid private-docs (3 runs) | `benchmark_results/hybrid_2026-07-05_*.json` (per-checkpoint grades, full reports) |
| SimpleQA parity | `benchmark_results/simpleqa_2026-07-04_14-*.json` |
| Report head-to-head (n=8) | `benchmark_results/reports_2026-07-04_14-33-21_n8.json` (per-topic verdicts, full reports) |
