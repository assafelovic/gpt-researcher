# Context Filter

Each research sub-query scrapes several pages, and only some of each page helps answer the question. Before anything reaches the LLM, GPT Researcher cuts the pages into passages and keeps the ones worth using. Report chat uses the same step to pick the parts of a report that answer your message. `CONTEXT_FILTER` chooses how:

| value | how passages are chosen | needs |
|---|---|---|
| `auto` (default) | `jev` when `TYPESAFE_API_KEY` is set, otherwise `keyword` | nothing |
| `jev` | [TypeSafe's Jev](https://docs.typesafe.ai/) scores how useful each passage is for the question; the best are kept | `TYPESAFE_API_KEY` |
| `keyword` | BM25 keyword ranking, computed locally | nothing |
| `embeddings` | embedding similarity to the question | an `EMBEDDING` provider |
| `none` | no filtering: every page goes to the LLM in full | nothing |

**Nothing is required.** If a Jev call fails, or the embedding model can't be built, GPT Researcher falls back to `keyword`, so no setting can leave a run without context. Only the `embeddings` mode ever builds an embedding model.

## Results

We replayed 28 research tasks (20 [SimpleQA](https://openai.com/index/introducing-simpleqa/) questions with known answers and 8 open-ended ones) through every filter, using the same scraped pages and the same writer model, so that only the filter changed. Full method, tables and reproduction steps are in [`evals/context_filter`](https://github.com/assafelovic/gpt-researcher/tree/main/evals/context_filter).

| filter | relevant passages kept | head-to-head vs embeddings | filter time (median) | cost per report |
|---|---|---|---|---|
| **jev** | **73%** | **15 wins · 10 ties · 3 losses** | 1.7s | $0.115 |
| keyword | 51% | 14 wins · 8 ties · 6 losses | 0.02s | $0.116 |
| embeddings | 46% | — | 1.0s | $0.117 |
| none | — | 13 wins · 11 ties · 4 losses | — | $0.192 |

- **Jev** is the most accurate filter, for the same cost as embeddings. Its gain comes from its threshold: a calibrated usefulness score can say that nothing else on a page is worth including, which a similarity score can't.
- **Keyword** is the fallback that needs nothing. It matched or beat embeddings on every measure, and runs in milliseconds with no API call. Keeping only passages that score at least half as well as the best one is what makes it work; plain top-10 keyword ranking lost to embeddings.
- **None** writes the broadest reports on open-ended questions, but costs 65% more per report and sent up to 108k tokens to the writer on a standard report. Use it when quality matters more than cost, and not with detailed or deep research, which run many more sub-queries.
- Writing the report takes about 45 seconds with every filter, so a run's total time changes only by the filter step.

## Configuration

```bash
export TYPESAFE_API_KEY=...          # enables jev under the default `auto`
export CONTEXT_FILTER=auto           # auto | jev | keyword | embeddings | none

export JEV_MIN_SCORE=1.5             # 0-3 usefulness a passage needs to be kept
export JEV_CONCURRENCY=64            # parallel Jev calls per process
export JEV_CHUNK_SIZE=1000           # characters per scored passage

export KEYWORD_RELATIVE_THRESHOLD=0.5  # keep passages scoring >= this fraction of the best
export KEYWORD_MAX_RESULTS=25          # most passages kept per sub-query
```

Jev's usefulness scale runs from 0 (unrelated) through 1 (same topic, doesn't help) and 2 (partially answers or gives useful supporting facts) to 3 (directly answers with specifics). The default threshold of 1.5 keeps passages that at least partially answer the question.

Embeddings are still used for vector stores you pass in yourself (`vector_store=`), and, when an embedding model is available, to spot overlap between sections of detailed reports; without one, that check uses keyword ranking too.
