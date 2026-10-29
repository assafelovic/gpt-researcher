# research_eval

Evaluation of gpt-researcher's whole pipeline (query decomposition, retrieval,
writing) with reference-free metrics. Built alongside the older `quality_eval/`,
which is left untouched until the two have been compared on the same runs.

Design: `eval-design/` (README, infrastructure, retrieval-metrics,
generation-metrics). This package implements the infrastructure, the retrieval
metrics and the generation metrics (plus toxicity / bias).

## Principles

- **Run and score are separate.** A run writes one frozen JSON archive; scoring
  only reads archives. Changing a metric, prompt or judge means re-scoring, never
  re-running the agent.
- **Scores only.** Every metric is listed on its own; there is no overall score
  and no diagnosis in the system.
- **The library is not modified.** All capture is monkeypatching, reverted on exit.
- **All modes:** `default`, `detailed`, `deep`.

## Pipeline

```
dataset/questions_*.jsonl -> runner.py -> capture.py (hooks) -> runs/<dataset>/<run_id>.json
                                                                    |
                                       score.py -> metrics/ -> results/<run_id>/<scorer_version>.json
                                                      ^
                                     cache/research_eval.sqlite, judge.py, prompts.py
```

| Module | Role |
|---|---|
| `tracing.py` | Span tracer. `contextvars` carries the current span, so `asyncio.gather` and nested researchers attach correctly. OTel field names, no OTel dependency. |
| `capture.py` | Hooks H1-H6 plus researcher, subtopic, cost and health hooks. |
| `chunks.py` | Splits a sub-query's context string back into `Source:/Title:/Content:` chunks. |
| `archive.py` | Archive schema, write-once save, `RunArchive` with derived views (span tree, decompositions, retrieval units, URL -> chunk index, parsed report). |
| `report_parser.py` | Python-Markdown (+tables) -> sections, paragraphs, citations, evidence, parse warnings. |
| `cache.py` | One SQLite file: `question`, `domain`, `llm`, `embedding` namespaces. |
| `judge.py` | Cached judge (model from `evals/judge.py`) and cached embedder (repo `EMBEDDING` setting). |
| `prompts.py` | Versioned rubric prompts; version + content hash go into cache keys and results. |
| `key_points.py` | Per-question key points: frozen file > cache > one judge call. |
| `citation_audit.py` | Shared paragraph-level judge audit: claims, ALCE sentence checks, which chunks were used. |
| `metrics/` | `Metric` interface and registry; `retrieval/` holds the nine retrieval metrics, `generation/` the thirteen generation ones. |
| `scoring.py` | Runs metrics on an archive; results keyed by run_id + scorer version. |
| `runner.py`, `score.py` | CLIs. |

## Usage

```bash
# Run (needs OPENAI_API_KEY, TAVILY_API_KEY). Writes runs/questions_v0/<run_id>.json
python -m evals.research_eval.runner --modes default --limit 2
python -m evals.research_eval.runner --modes default,detailed,deep --questions q001,q002

# Score (never runs the agent)
python -m evals.research_eval.score evals/research_eval/runs/questions_v0/*.json
python -m evals.research_eval.score RUN.json --rules-only           # zero-cost metrics
python -m evals.research_eval.score RUN.json --metrics plan_adherence,query_relevance
```

The judge model is `EVAL_JUDGE_MODEL` (default in `evals/judge.py`). Re-scoring an
archive with unchanged metrics replays every judge and embedding call from the cache.

## Archive (schema 1.0)

```json
{
  "schema_version": "1.0",
  "meta": {"run_id", "trace_id", "question_id", "query", "dataset_version", "agent_commit",
           "started_at", "duration_s", "cost_usd", "status", "error",
           "config": {"report_type", "mode", "context_filter", "context_filter_resolved",
                      "worker_model", "embedding", "retrievers", "max_iterations",
                      "max_search_results_per_query", "breadth", "depth"},
           "health": {"jev_fallback", "embedding_fallback", "subquery_errors",
                      "web_search_errors", "mcp_fallback", "context_parse_warnings"}},
  "spans":  [{"span_id", "parent_id", "name", "attributes", "start_time", "end_time", "status", "error"}],
  "chunks": {"<chunk_id>": {"url", "title", "content", "jev_score"}},
  "report": {"markdown": "..."}
}
```

Span names and what they carry:

| Span | Hook | Attributes |
|---|---|---|
| `run` | runner | query, mode |
| `research` | `GPTResearcher.conduct_research` | query, report_type, parent_query; deep: research_goal, learnings, follow_ups |
| `plan` (H1) | `ResearchConductor.plan_research` | query, sub_queries (as planned, before the core query is appended) |
| `deep_plan` (H2) | `DeepResearchSkill.generate_research_plan` | query, questions |
| `deep_level` (H2) | `DeepResearchSkill.deep_research` | query, breadth, depth, serp_queries [{query, goal}] |
| `subtopics` | `GPTResearcher.get_subtopics` | query, subtopics |
| `sub_query` (H4) | `ResearchConductor._process_sub_query` | query, is_core_query, chunk_ids, proposed_urls / new_urls (H3), context_filter / pages_in (H6) |
| `initial_results` (H5) | `ResearchConductor._get_context_from_initial_results` | query, chunk_ids, proposed_urls / new_urls |

Tree shape: `sub_query` spans hang under the `plan` that proposed them;
`initial_results` hangs under its `research`. In deep mode each branch's nested
`research` hangs under its `deep_level`, and the next level hangs under the branch
whose follow-up questions produced it (matched by the research goal in its query).

## Retrieval metrics

| Category | Metric | Value | LLM cost per run |
|---|---|---|---|
| Query | `decomposition_coverage` | key points some sub-query is aimed at / K; one judge call maps key points to sub-queries (embedding cosine only as a no-judge fallback) | key points: 1 per question, cached; mapping: 1 |
| Query | `subquery_redundancy` | sibling pairs with symmetric BM25-weighted overlap >= 0.6 / pairs (lower is better) | 0 |
| Query | `decomposition_tree_quality` | mean of judge total / 8 per parent (coverage, specificity, searchability, relevance) | 1 per parent |
| Query | `plan_adherence` | planned sub-queries that returned chunks / planned | 0 |
| Source | `source_authority` | mean authority over sources; rule tiers, then global domain cache, then one batched call | <= 1, tends to 0 |
| Source | `source_diversity` | distinct domains / sources; entropy in details | 0 |
| Efficiency | `citation_utilization` | retrieved URLs the body cites / retrieved URLs; chunk level in details (judged via the citation audit when a judge is set, else rule-based) | 0 (audit shared) |
| Efficiency | `query_relevance` | mean of judge total / 10 per search step + material (Q1-Q5 rubric); steps = sub-queries + each initial search; material = one best chunk per URL, 12k chars | 1 per step with material |
| Efficiency | `retrieval_overlap` | search results already seen / proposed (lower is better) | 0 |

Every result carries `version`, `higher_is_better`, `details`, `skipped` (a reason,
when it could not run) and, for LLM metrics, `llm` (judge model, prompt versions and
hashes, judge requests, cache hits, actual API calls, errors).

Thresholds (0.6 redundancy, 0.5 for the utilization chunk diagnostic and for the coverage embedding fallback) are uncalibrated
first guesses; `details` keeps the underlying similarities so they can be tuned
against human labels. Override per scoring run via `ScoringContext.options`.

## Implementation notes

- **Which URLs are "retrieved".** Source and efficiency metrics use the URLs of the
  chunks that reached the context, i.e. what the writer could read, not every URL
  the search proposed.
- **URL matching** ignores scheme, `www.`, trailing slash and fragment.
- **Citation utilization** is URL-level and rule-based. Which chunk a claim actually
  rests on comes from the generation side's citation audit: with a judge, `details`
  adds `chunk_level_judged` / `chunks_used_judged`. The rule-based chunk
  diagnostic (kept for `--rules-only`) only counts a chunk as used when a paragraph citing its URL
  matches it (BM25-IDF-weighted term share, bounded in [0, 1]); chunks of uncited URLs
  whose content the report echoes are listed as `echoed_uncited`, since many sources
  repeat the same facts. A first LLM-judged version marked every borderline chunk as used,
  uncited sources and page navigation text included.
- **Source diversity** is still a domain count (distinct domains / sources, entropy).
  On this pipeline it saturates near 1.0 (5 results per query, URLs de-duplicated), so it
  separates runs poorly; a better formulation is open.
- **Plan adherence** counts plan sub-queries, deep-research SERP queries and detailed
  subtopics. Deep-research clarifying questions are folded into one combined query by
  the library, so they are not counted.
- **Query relevance** judges every executed sub-query except the run's own core query
  (nested researchers' root queries, i.e. SERP queries and subtopics, are included), plus each
  researcher's initial planning search. The judge sees one chunk per source URL, so a step
  with 20+ chunks is judged on its breadth, not on the first site's first chunks.
- **Context formats.** Chunks are split from the default `pretty_print_docs` format.
  MCP results and the Granite prompt families use other formats; such text is kept as
  one chunk with `url = null` and counted in `health.context_parse_warnings`.
- **Cost.** `cost_usd` sums every `add_costs` call across nested researchers. The
  library's deep-research planning calls do not report cost, so deep runs under-count.

## Validation so far

One real run: q001, default mode (about 135 s, $0.17 worker cost, 25 Tavily results).
Each metric's score was checked by hand against the report, spans and chunks.

| Metric | Score | Verdict |
|---|---|---|
| `retrieval_overlap` | 0.400 | Correct; flags a real waste: the core query is searched twice (initial search + appended core sub-query), 5 duplicate results |
| `decomposition_tree_quality` | 0.875 | Rubric evidence holds; the one deduction (non-EU Europe missing) is the report's real gap |
| `source_authority` | 0.554 | Domain scores plausible; the low score reflects zero official sources |
| `plan_adherence` | 1.000 | Correct; little room to vary in default mode |
| `subquery_redundancy` | 0.000 | Correct for 3 sub-queries; sample too small to judge |
| `decomposition_coverage` | 0.625 | Correct after v2 (v1 embedding matching had 3 of 8 points wrong) |
| `query_relevance` | 0.800 | v2 shows the judge every source URL (v1 saw 5-7 of 11-23 chunks) and scores the initial search |
| `citation_utilization` | 0.692 | 9 of 13 retrieved URLs cited; v1's LLM chunk level marked uncited sources as used |
| `source_diversity` | 1.000 | Computed correctly but saturates; formulation open |

Re-scoring the same archive replays every judge call from the cache and gives identical
numbers. `query_relevance` and `decomposition_coverage` answer different questions and
can legitimately differ: material on a key point can arrive from a search not aimed at it.

## Generation metrics

| Category | Metric | Value | LLM cost per run |
|---|---|---|---|
| Writing | `comprehensiveness` | (full + 0.5 partial key points) / K; uncovered points that a retrieved chunk seems to discuss are listed as `omitted_but_retrieved` | 1 (+ key points, shared) |
| Writing | `insight` | weighted rubric score / 10; rubric (3-5 criteria) generated once per question | rubric: 1 per question, cached; scoring: 1, shared with readability |
| Writing | `readability` | same, readability criteria | shared |
| Writing | `instruction_following` | passed / 7 rule checks: min words, one title, clean headings, no TOC, references, in-text citations, cites only retrieved URLs | 0 |
| Writing | `topic_relevance` | (yes + idk) / paragraphs | 1 per ~20k chars |
| Citation | `citation_recall` | ALCE: citing sentences supported by their own sources / citing sentences | audit (below) |
| Citation | `citation_precision` | ALCE: precise citations / citations (sentence-URL pairs) | audit |
| Citation | `citation_coverage` | references cited in the body / references (URL level; formerly `citation_faithfulness`) | 0 |
| Citation | `effective_citations` | count of citations their source supports (FACT style) | audit |
| Hallucination | `faithfulness` | mean claim score in [-1, 1]: supported 1, inferred 0.5 / 0.4 / 0.3, unsupported 0, contradicted -1 | audit |
| Hallucination | `fact_grounding` | numbers and capitalised names found verbatim in the cited chunks / checked | 0 |
| Other | `toxicity` | flagged opinions / opinions (lower is better) | 1 per ~15k chars, shared with bias |
| Other | `bias` | same, bias flag (gender, politics, race, religion, geography) | shared |

**Citation audit** (`citation_audit.py`), one judge call per paragraph, shared by the
citation and faithfulness metrics and by `citation_utilization`:

- Citations are placed per sentence by link position (`report_parser.cited_sentences`;
  a citation after the full stop, e.g. APA style "... rose. (Didit, 2026; Norton, n.d.)",
  goes with the sentence before it, and no sentence ends inside parentheses).
- Citation scope: by default a citation vouches for its sentence plus the uncited
  sentences right before it (back to the previous citation), because the writer is
  told to cite "at the end of the sentence or paragraph" and mostly cites once per
  paragraph. Strict per-sentence ALCE: option `citation_scope="sentence"`. On q001
  the strict reading scored recall 0.37: it judged each paragraph's citation only
  against its closing, usually analytical, sentence.
- Material: for each cited URL, its retrieved chunks that best match the paragraph
  (first the best chunk for each sentence, then by match with the paragraph; up to 12,
  24k chars per paragraph, so most cited pages are shown whole: with 3 chunks per URL a
  fact on a long page was judged unsupported because its chunk was not shown); a cited URL that was never
  retrieved is shown as unavailable and its sentence counts as unsupported without
  asking. Paragraphs without citations (>= 80 chars) get the 4 best-matching chunks of
  everything retrieved; the judge skips them when they are opinion or transition.
- The judge returns the paragraph's claims (6-level verdict + passage ids, which map
  to `used_chunk_ids`) and, per citing sentence, joint support plus per source
  `alone` / `rest_suffice`. ALCE precision is computed as in its reference code: a
  citation of an unsupported sentence is imprecise, and with several citations one is
  irrelevant only when it does not support alone and the rest still do.
- Shared calls are reported by every metric that reads them (`llm.shared`), so do not
  sum `api_calls` across those metrics.

Notes:

- Faithfulness and the rule check are listed separately (design §3.2 called them one
  composite score; there are no combined scores in this system).
- Comprehensiveness uses one judge call, not an embedding pre-pass: on the retrieval
  side embedding matching got 3 of 8 key points wrong.
- `instruction_following` reads `config.total_words` (recorded by the runner from now
  on); older archives fall back to option `min_words` (default 1200, the repo default).
- `fact_grounding` is uncalibrated: a paraphrased or unit-converted figure counts as
  missing; per-paragraph `missing` lists are in `details` for review.

## Not yet done

- Source diversity formulation (domain ratio saturates; under research).
- Generation metrics validated on real archives (offline tests only so far).
- Per-paragraph sampling twice for a more stable faithfulness verdict (design §5).
- Perturbation tests on a frozen archive (does each metric move the expected way when a
  known problem is injected), then judge calibration with a small human-labelled set.
- Runs of detailed and deep mode with real APIs (covered so far by offline tests only).
- Question set size and composition (`dataset/questions_v0.jsonl` is a placeholder).
- Old-vs-new comparison against `quality_eval`; evaluator stability benchmarks.
