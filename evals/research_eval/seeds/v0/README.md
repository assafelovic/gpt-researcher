# Seed samples v0

Real runs kept as seed samples for a future benchmark of **this evaluation system**
(stability, sensitivity, perturbation tests, judge calibration), not of gpt-researcher.
Each sample is a frozen archive plus the scores the evaluator gave it, so later
versions of the evaluator can be compared on identical input.

All three runs: question q001 ("What regulatory changes are affecting the crypto
industry in Europe?"), `questions_v0`, agent commit `d06123bf` (`-dirty` only because
of untracked run files), worker models `openai:gpt-5.4` (smart / fast / strategic),
Tavily retriever, 1200 target words. Judge `gpt-6-luna`, scorer `0.1+d5e17daa`.

| Sample | run_id | Duration | Worker cost | Report words | Chunks | Judge errors |
|---|---|---|---|---|---|---|
| `q001_default` | `20261029T234054_q001_default_3fc58f` | 101 s | $0.15 | 2,400 | 45 | 0 |
| `q001_detailed` | `20261029T234235_q001_detailed_2cfdba` | 382 s | $0.65 | 8,307 | 230 | 0 |
| `q001_deep` | `20261029T234921_q001_deep_ff96d2` | 1,278 s | $0.35* | 2,836 | 379 | 0 |

\* Deep mode (breadth 2, depth 2): 18 "LLM returned empty response" retries in
`process_research_results` (`max_tokens=4000` with high reasoning effort on gpt-5.4,
so the budget goes to reasoning). Failed attempts are not in `cost_usd`, so the real
cost is higher.

## Files

| File | What |
|---|---|
| `q001_*/archive.json` | Run archive (schema 1.0): meta, spans, chunks, report. Input to `score.py`. |
| `q001_*/report.md` | The report, extracted from the archive for reading. |
| `q001_*/scores.json` | Full scoring record: 22 metrics with details, judge prompts and call counts. |
| `q001_deep/scores_failed_no_credits.json` | First deep scoring, cut off when the OpenAI account ran out of credits (429). Kept as a judge-failure sample: it exposed `source_authority` scoring 34 of 53 domains with rule fallbacks and reporting 0.516 instead of skipping, and the audit metrics skipping with a misleading reason ("no citations"). Both fixed. |
| `q001_deep/score_failed_no_credits.log` | Console output of that run. |
| `run_default_detailed.log`, `q001_deep/run.log` | Agent console logs (default and detailed ran in one process; stdout and stderr interleave). |
| `score.log` | Console output of the final scoring of all three. |

## Scores

| Metric | default | detailed | deep |
|---|---|---|---|
| decomposition_coverage | 0.375 | 0.875 | 0.625 |
| subquery_redundancy (lower better) | 0.000 | 0.000 | 0.000 |
| decomposition_tree_quality | 0.875 | 0.950 | 0.875 |
| plan_adherence | 1.000 | 1.000 | 1.000 |
| source_authority | 0.630 | 0.538 | 0.559 |
| source_diversity | 1.000 | 0.907 | 0.779 |
| citation_utilization | 1.000 | 0.930 | 0.221 |
| query_relevance | 0.775 | 0.675 | 0.662 |
| retrieval_overlap (lower better) | 0.520 | 0.471 | 0.533 |
| comprehensiveness | 0.688 | 0.750 | 0.500 |
| insight | 0.650 | 0.675 | 0.625 |
| readability | 0.675 | 0.525 | 0.500 |
| instruction_following | 1.000 | 0.857 | 1.000 |
| topic_relevance | 1.000 | 0.946 | 1.000 |
| citation_recall | 0.513 | 0.382 | 0.417 |
| citation_precision | 0.396 | 0.368 | 0.359 |
| citation_coverage | 1.000 | 0.889 | 1.000 |
| effective_citations | 21 | 45 | 9 |
| faithfulness | 0.752 | 0.667 | 0.614 |
| fact_grounding | 0.924 | 0.961 | 0.933 |
| toxicity (lower better) | 0.000 | 0.000 | 0.000 |
| bias (lower better) | 0.000 | 0.000 | 0.000 |

Re-scoring default and detailed replayed every judge call from the cache and gave
identical numbers. These scores are not yet checked by hand; that review, and
human labels, are what turn these seeds into benchmark items.

## Re-scoring

```bash
python -m evals.research_eval.score evals/research_eval/seeds/v0/q001_*/archive.json \
    --results-dir /tmp/seed_scores --cache /tmp/seed_cache.sqlite   # fresh judge calls
```

Without the judge cache (`cache/`, not committed) every judge call is made again,
so LLM-judged scores can differ run to run; that spread is itself a stability sample.
