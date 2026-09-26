# Context Filter

Each research sub-query scrapes several pages. Before anything reaches the report writer, GPT Researcher cuts those pages into chunks and keeps only the ones worth using. `CONTEXT_FILTER` chooses how:

| value | how chunks are chosen | needs |
|---|---|---|
| `auto` (default) | `jev` when `TYPESAFE_API_KEY` is set, otherwise `embeddings` | — |
| `jev` | [TypeSafe's Jev](https://docs.typesafe.ai/) scores every chunk on how useful it is for answering the sub-query; the best-scoring chunks are kept | `TYPESAFE_API_KEY` |
| `embeddings` | chunks most similar to the sub-query by embedding cosine similarity | an `EMBEDDING` provider |
| `none` | no filtering: every scraped page goes to the writer in full | — |

## Which one to use

We benchmarked all of them on 28 research questions, replaying the same scraped pages through each filter (full results in [`evals/context_filter`](https://github.com/assafelovic/gpt-researcher/tree/main/evals/context_filter)):

- **`jev`** picked relevant chunks 73% of the time against 46% for embeddings, and its reports won 15–3 in blind head-to-head comparisons, at the same cost per report (both filters cost well under a cent). With `jev`, a standard research run never builds an embedding model, so you don't need an embeddings provider or key.
- **`none`** gave the richest reports on broad, open-ended questions, but cost 65–83% more per report and sent up to 108k tokens to the writer on a *standard* report. Use it when report quality matters more than cost, and not with detailed or deep research, which run many more sub-queries.
- **`embeddings`** remains the fallback when no TypeSafe key is set, and whenever a Jev call fails.

## Configuration

```bash
export TYPESAFE_API_KEY=...        # enables jev under the default `auto`
export CONTEXT_FILTER=auto         # auto | jev | embeddings | none
export JEV_MIN_SCORE=1.5           # 0-3 usefulness score a chunk needs to be kept
export JEV_CONCURRENCY=64          # parallel Jev calls per process
export JEV_CHUNK_SIZE=1000         # characters per scored chunk
```

Jev's usefulness scale runs from 0 (unrelated) through 1 (same topic, doesn't help) and 2 (partially answers or useful supporting facts) to 3 (directly answers with specifics). The default threshold of 1.5 keeps chunks that at least partially answer the question. That threshold is where most of the quality gain comes from: unlike a similarity score, it can say that nothing else on a page is worth including.

Embeddings are still used for local document vector stores you pass in, for the written-content deduplication in detailed reports, and for report chat.
