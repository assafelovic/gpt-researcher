# Seed samples v0

Three real runs kept as fixed input for checks on **this evaluation system**
(integrity, perturbation tests, re-scoring), not as a benchmark of gpt-researcher.
The tests read `q001_*/archive.json`, and `dataset/clean_bases/` builds on
`q001_default`.

All three runs: question q001 ("What regulatory changes are affecting the crypto
industry in Europe?"), `questions_v0`, agent commit `d06123bf`, worker models
`openai:gpt-5.4` (smart / fast / strategic), Tavily retriever, 1200 target words.

| Sample | run_id | Duration | Worker cost | Report words | Chunks |
|---|---|---|---|---|---|
| `q001_default` | `20261029T234054_q001_default_3fc58f` | 101 s | $0.15 | 2,400 | 45 |
| `q001_detailed` | `20261029T234235_q001_detailed_2cfdba` | 382 s | $0.65 | 8,307 | 230 |
| `q001_deep` | `20261029T234921_q001_deep_ff96d2` | 1,278 s | $0.35* | 2,836 | 379 |

\* Deep mode (breadth 2, depth 2): 18 "LLM returned empty response" retries in
`process_research_results` (`max_tokens=4000` with high reasoning effort on gpt-5.4,
so the budget goes to reasoning). Failed attempts are not in `cost_usd`, so the real
cost is higher.

## Files

| File | What |
|---|---|
| `q001_*/archive.json` | Run archive (schema 1.0): meta, spans, chunks, report. Input to `score.py`. |
| `q001_*/report.md` | The report, extracted from the archive for reading. |

## Scoring

```bash
python -m evals.research_eval.score evals/research_eval/seeds/v0/q001_*/archive.json \
    --results-dir /tmp/seed_scores --cache /tmp/seed_cache.sqlite
```

Without a judge cache every judge call is made again, so LLM-judged scores can
differ run to run; `stats.py --noise` measures that spread.
