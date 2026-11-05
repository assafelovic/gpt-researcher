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
python -m evals.research_eval.score RUNS --dry-run                  # count uncached judge calls, call nothing
python -m evals.research_eval.score RUNS --max-calls 300            # cap uncached judge calls
python -m evals.research_eval.score RUNS --judge-salt noise1        # ask the judge again (noise control)

# Perturbation test: does each metric get worse when the run does? (perturb.py)
python -m evals.research_eval.perturb make RUN.json [RUN.json ...] --out DIR
python -m evals.research_eval.score DIR/*__*.json --results-dir DIR/results   # not manifest.json
python -m evals.research_eval.perturb report DIR/manifest.json --results-dir DIR/results

# Integrity audit: is every input counted, and counted once? (integrity.py, no model calls)
python -m evals.research_eval.integrity RUNS/*.json --results-dir RESULTS --json integrity.json
```

The integrity audit checks the bookkeeping, not the judgments: for each archive and its
latest score record it compares counts that must agree and measures what each limit
cut. Report: body links = parsed citations, body words in parsed paragraphs, which
paragraphs the citation audit leaves out and why, References sub-headings, whether the
report stops part-way. Trace: chunk ids resolve, no chunk outside a search step, no page
swallowed by the chunk before it, chunks without a URL, failed deep steps. Prompts: the
whole report within `REPORT_CHARS`, tree-quality path entries cut, audit passages cut at
`PASSAGE_CHARS`, chunks of cited pages left to the recheck, query-relevance URLs shown.
Audit: every audited paragraph judged once, judge errors, the audit's sources = the
paragraph's citations, claims tied to items that exist, the same fact claims in
citation recall's and faithfulness's denominators, every unsupported fact rechecked.
Metrics: skips, judge errors, items a judge reply skipped. Each check is ok / note (left
out by design, amount given) / warn (lost or cut) / fail (counts disagree); any fail
sets exit code 1.

The perturbation test checks the evaluator, not the agent. `perturb make` copies an
archive and injects one known defect per copy, rule-based and deterministic: half the
sections dropped, body links stripped, citations pointed at unrelated retrieved pages,
figures changed, off-topic paragraphs, analysis removed, structure scrambled, toxic or
biased opinions added, sub-queries made near-copies, off-topic material for half the
search steps. Each copy names the metrics that should move and which way. `__base` is an
unchanged copy (it replays the original scores from the cache); `__noise` is another,
to be scored with `--judge-salt` so the judge's own spread sets how large a change has
to be. `perturb report` prints, per defect and metric, the change and a verdict
(pass / weak / FAIL), plus the other metrics that moved.

The judge model is `EVAL_JUDGE_MODEL` (default in `evals/judge.py`). Re-scoring an
archive with unchanged metrics replays every judge and embedding call from the cache.
At the end, `score` prints the judge's call count, cache hits and the input / output
tokens of uncached calls (from the provider's usage metadata), so scoring cost is
measured rather than guessed.

Failed runs are not scored: when the agent raised (`meta.status != "ok"`) or finished
without a real report (no citations and under 1,000 characters, e.g. deep research's
fallback sentence after every sub-query failed), every metric is skipped with
`failed run: <reason>` and the record carries `run_status: "failed"`. `--score-failed`
scores them anyway.

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

| Group | Metric | Value | LLM cost per run |
|---|---|---|---|
| Query quality | `decomposition_coverage` | key points some sub-query is aimed at / K (deep research's clarifying questions are not sub-queries: they are folded into one query, never searched); one judge call maps key points to sub-queries (embedding cosine only as a no-judge fallback) | key points: 1 per question, cached; mapping: 1 |
| Query quality | `subquery_redundancy` | query-tree nodes that repeat another node / all nodes (lower is better); nodes = every searched query below the run's question, branches (a researcher's own question, split further; its repeat search is the same node) and leaves (planned sub-queries), with or without new material; any two nodes are compared, at any layer and in any branch, except a node and the nodes it was split from; one judge call sees every node in search order with its ancestors' numbers and marks each that asks for the same information as an earlier one in other words (another perspective, source, period, place, subtopic or a narrower part is not a repeat); marks on an ancestor are dropped; the call is made 3 times and a node is a repeat when 2 of them mark it (`details.unstable` lists split verdicts); `details.per_layer`, `details.per_kind` (branch / leaf), `details.same_layer` and `details.same_parent`; without a judge, sibling pairs with symmetric BM25-weighted overlap >= 0.6 / pairs (`details.method`) | 3 |
| Query quality | `decomposition_tree_quality` | mean parent score; per parent (deep research's clarifying questions left out) the judge sees the path from the question down to the parent and answers four yes/no checks per child (narrower than the parent, searchable as is, serves the parent, still serves the original question) and lists the parent's aspects (at most 6) with the children aimed at each; parent score = (pass rate of each check + aspect coverage) / 5; `details.checks`, `details.coverage`, `details.weak_children` | 1 per parent |
| Source quality | `source_authority` | mean authority over the report's citations (one per paragraph-URL pair); mean over all retrieved sources in `details.retrieved_mean`; a report whose body cites nothing is skipped (no fallback to the retrieved mean); rule tiers (subdomains included), then global domain cache, then one batched call | <= 1, tends to 0 |
| Source quality | `source_diversity` | Gini-Simpson diversity of cited domains with Hurlbert's small-sample correction (PIE), citation = paragraph-URL pair: chance that two citations drawn at random are from different domains, n/(n-1) × (1 − Σp²), in [0, 1]; unbiased, so citing more of the same mix does not by itself raise it, though a report drawing on more domains scores higher (r = 0.83 with word count on v12, entropy, the v3 value, 0.93); unlike Pielou evenness it does not give full marks to two evenly cited domains; a body that cites nothing scores 0 (no fallback to the retrieved sources); details give entropy, 2^H, evenness, HHI and effective domains for citations and retrieved sources | 0 |
| Source quality | `source_recency` | share of the cited sources (distinct URLs that were retrieved) dated in the run's year or the year before (`recency_years`, default 1); date = a date in the URL path, else the latest year named in the title or retrieved text, years after the run ignored (forecasts); undated sources are left out of the value and counted (`undated`); `retrieved_share` gives the same share over every source that reached the writer, `per_citation` weights by body citations. Dates sources, not facts; meant for time-sensitive questions | 0 |
| Retrieval quality | `plan_adherence` | planned sub-queries whose step was carried out / planned: the step returned chunks and, for deep research, did not fail afterwards (a step whose result processing raised is dropped, so its material never goes on); `details.retrieval_delivery` = planned sub-queries that returned chunks / planned (the v2 value), `failed_after_retrieval` lists the difference | 0 |
| Retrieval quality | `retrieval_overlap` | search results already seen / proposed (lower is better), leaving out each researcher's repeat search of its own question; `details.with_core_repeats` keeps the old rate | 0 |
| Retrieval quality | `material_coverage` | (full + 0.5 partial key points) / K, graded on the retrieved material before any writing: per key point the evaluator picks the 6 best BM25 passages (one per URL) from the chunks that reached the writer; one judge call per run grades every point; a lower bound (a point covered only in other words can be missed). Read per point beside decomposition_coverage (searched for?) and comprehensiveness (written?) | 1 (+ key points, shared) |
| Retrieval quality | `query_relevance` | mean of judge total / 10 per search step + material (Q1-Q5 rubric); steps = sub-queries + each initial search; material = one best chunk per URL, 12k chars | 1 per step with material |
| Retrieval quality | `source_utilization` (formerly `citation_utilization`) | retrieved URLs the body cites / retrieved URLs ("used" = cited: actual use cannot be told from the report); chunk level in details (judged via the citation audit when a judge is set, else rule-based); deep research adds `details.reasoning`: the URL funnel (retrieved URLs → URLs a learning names as its source → those the report cites) and chunks that reach the report through a learning | 0 (audit shared) |

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
| `source_utilization` | 0.692 | 9 of 13 retrieved URLs cited; v1's LLM chunk level marked uncited sources as used |
| `source_diversity` | 1.000 | Computed correctly but saturates; formulation open |

Re-scoring the same archive replays every judge call from the cache and gives identical
numbers. `query_relevance` and `decomposition_coverage` answer different questions and
can legitimately differ: material on a key point can arrive from a search not aimed at it.

## Generation metrics

| Group | Metric | Value | LLM cost per run |
|---|---|---|---|
| Writing quality | `comprehensiveness` | (full + 0.5 partial key points) / K; uncovered points that a retrieved chunk seems to discuss are listed as `omitted_but_retrieved`; a point the judge's reply skips scores none and is counted in `details.unanswered` | 1 (+ key points, shared) |
| Writing quality | `insight` | weighted rubric score / 10; rubric (3-5 criteria) generated once per question; `details.insights_found` records the insights the judge read | rubric: 1 per question, cached; scoring: 1, shared with readability |
| Writing quality | `readability` | same, readability criteria | shared |
| Writing quality | `toxicity` | number of opinions the judge flags as toxic (lower is better, 0 is the target); a count because a share of all opinions dilutes the same flagged sentences in a longer report; `details.rate` = flagged / opinions (the v1 value), `per_1k_words` | 1 per ~15k chars, shared with bias |
| Writing quality | `bias` | same, bias flag (gender, politics, race, religion, geography): number flagged | shared |
| Writing quality | `topic_relevance` | (yes + idk) / paragraphs | 1 per ~20k chars |
| Writing authority | `instruction_following` | passed / 8 rule checks (7 in detailed mode, whose TOC is inserted by code): min words, one title, clean headings, no TOC, references, in-text citations, cites only retrieved URLs, complete (the report does not stop part-way: open emphasis / link / code block, or a last paragraph without closing punctuation; `details.ending`) | 0 |
| Writing authority | `citation_recall` | per claim: fact claims supported by their own citations / all fact claims (as in ALCE, an uncited fact counts as unsupported). Claims come from the audit (checkable, atomic, self-contained; typed `fact` or `analysis`: the writer's own evaluation, ranking, recommendation or conclusion, which recall, precision, effective citations and the faithfulness value leave out; faithfulness reports it separately); supported = verdict "supported" (strict) and a passage it rests on is from a URL its own item cites. `details.cited_only` = supported cited claims / cited claims (are the citations given right?); `details.cited_share` = cited claims / all fact claims; `details.unit_level` keeps the former ALCE per-citing-unit value | audit (below) |
| Writing authority | `citation_precision` | per claim: citations that back a supported claim of their item / citations (item-URL pairs; items with no factual claim left out; in a table, each URL once per table, precise if it is for any row). `details.unit_level` keeps the ALCE value; `details.redundant_rate`: precise citations whose every backed claim another URL of the item also backs (corroboration, kept out of the value) | audit |
| Writing authority | `citation_coverage` | references cited in the body / references (URL level; formerly `citation_faithfulness`) | 0 |
| Writing authority | `effective_citations` | distinct pieces of evidence cited correctly per 1,000 words of report body: retrieved chunks a supported fact claim rests on through its own citations, near-duplicate chunks merged (symmetric BM25 overlap >= 0.8, no judge call); per 1,000 words because the count (the v3 value, `details.evidence`) grows with report length; a report that states facts but cites nothing scores 0; details also keep citation pairs and distinct URLs. A density: it rises when analysis is cut, so read it beside insight | audit |
| Writing authority | `fact_grounding` | numbers and capitalised names found in the cited chunks / checked (names: singular ~ plural, leading "the" ignored, 3+ word names ~ their acronym); numbers and names counted separately in `details` | 0 |
| Writing authority | `faithfulness` | mean fact-claim score in [-1, 1]: supported 1, inferred 0.5 / 0.4 / 0.3, unsupported 0, contradicted -1. Analysis claims (the writer's own evaluation, which a source rarely states) are reported beside it (`details.by_type.analysis`, `analysis_contradicted`) rather than averaged in, so adding analysis does not lower the score; the mean over all claims (the v1 value) is `details.all_claims` | audit |

**Citation audit** (`citation_audit.py`), one judge call per paragraph, shared by the
citation and faithfulness metrics and by `source_utilization`:

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
- The score record keeps the whole audit under `citation_audit` (every claim with its
  verdict and passages, every citing sentence with its ALCE checks), so a reviewer can
  see what the metrics counted, not only what they flagged.
- A line holding only citations ("Sources: (ESMA, 2026; EBA, 2025)") belongs to the
  table, list or paragraph above it, so a table cited on the line below is audited
  against its own sources. A table of contents is not audited.
- The writing judges (comprehensiveness, insight, readability) read the report's own
  Markdown minus references and URLs, so tables, headings and numbering look as the
  reader sees them.

Notes:

- Faithfulness and the rule check are listed separately (design §3.2 called them one
  composite score; there are no combined scores in this system).
- Comprehensiveness uses one judge call, not an embedding pre-pass: on the retrieval
  side embedding matching got 3 of 8 key points wrong.
- `instruction_following` reads `config.total_words` (recorded by the runner from now
  on); older archives fall back to option `min_words` (default 1200, the repo default).
- `fact_grounding` is uncalibrated: a paraphrased or unit-converted figure counts as
  missing; per-paragraph `missing` lists are in `details` for review.

## Generation validation so far

q001 default run (27 audited paragraphs, about 35 judge calls, about $0.02 per scoring).
Findings were checked by hand against the report and chunks.

| Metric | Score | Verdict |
|---|---|---|
| `comprehensiveness` | 0.750 | Plausible; the one partial point (stablecoin reserve / redemption rules) is thin in the report |
| `insight` | 0.625 | Criterion evidence holds; the low criterion (no national or UK comparison) is a real gap |
| `readability` | 0.700 | Holds; it spotted the malformed milestone table and unexplained acronyms |
| `instruction_following` | 0.857 | Correct; the writer mangled one CoinShares URL (repeated path segment), so a cited URL was never retrieved |
| `topic_relevance` | 1.000 | Plausible for this report; untested on a report with padding |
| `citation_coverage` | 1.000 | Correct: all 9 references are cited in the body |
| `fact_grounding` | 0.976 | 165 tokens; the 4 misses are acronyms (KYC, TFR, AML, CFT) absent from the cited pages |
| `faithfulness` | 0.726 | Flagged claims are real embellishments (e.g. "DAC8 is less visible than MiCA", onboarding effects) after the fixes below |
| `citation_recall` | 0.300 | Low because the writer ends most paragraphs with its own analysis under the same citation; strict ALCE fails the whole unit. Kept strict on purpose: whether an inference is reasonable is hard to judge, and an unreasonable one should not sit under a citation (faithfulness gives inferences partial credit) |
| `citation_precision` | 0.255 | Tracks recall (ALCE counts citations of unsupported units as imprecise); only 1 over-citation |
| `effective_citations` | 6 | Count of unit-URL citations a source fully supports |
| `toxicity` / `bias` | 0 / 0 | No flagged opinions |

Fixed along the way: APA citations after the full stop ("(Didit, 2026; Norton, n.d.)")
became their own "sentences"; scoring a paragraph-end citation against only the last
sentence (recall 0.37 for the wrong reason); and showing 3 chunks per cited URL, which
made the judge call passporting unsupported although the cited page states it.

## Not yet done

- Citation recall / precision moved from citing units (often a whole paragraph with 3–6
  claims, failed by one inferred claim) to claims (audit 7, 2026-11-01); re-score and review.
- Insight / readability judge prompt: scores barely separate the modes (0.68 / 0.69 / 0.68
  over five questions); polish the prompt later.

- Source diversity formulation (domain ratio saturates; under research).
- Generation metrics: validated on one archive only (q001, below).
- Per-paragraph sampling twice for a more stable faithfulness verdict (design §5).
- Perturbation tests on a frozen archive (does each metric move the expected way when a
  known problem is injected), then judge calibration with a small human-labelled set.
- More real runs: one each of default, detailed and deep (q001) are saved as seed samples in
  `seeds/v0/` (archive, report, scores, logs), not yet reviewed by hand. q002–q005 were run
  once per mode on 2026-10-31; their archives are not in the repo.
- Question set size and composition (`dataset/questions_v0.jsonl` has five questions).
- Old-vs-new comparison against `quality_eval`; evaluator stability benchmarks.
