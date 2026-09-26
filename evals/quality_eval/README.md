# quality_eval — Report Quality Evaluation for Autonomous Research Agents

Evaluate the quality of a GPT-Researcher report on **any open-ended query, with no
ground-truth answer required**. Where `simple_evals` needs a labelled dataset and
`hallucination_eval` gives a binary check, `quality_eval` scores a report across
several interpretable dimensions of *how well it was researched and written*.

It follows the metric abstraction of established frameworks (DeepEval / RAGAS),
and **extends it for autonomous research** — evaluating not just the answer, but
the quality of the sources the agent found on its own.

## What it measures

| Group | Aligns with | Metric | Question it answers |
|---|---|---|---|
| **Faithfulness** | RAGAS Faithfulness | `unsupported_claim` | Are the report's claims grounded in the sources? |
| **Answer Relevancy** | RAGAS answer relevancy | `subtopic_coverage` | Does it cover the subtopics a thorough report should? |
| **Source Quality** | *extension (autonomous agent)* | `source_authority`, `source_diversity` | Are the sources the agent found authoritative and varied? |
| **Citation** | ALCE citation precision | `citation_faithfulness` | Are the listed references actually cited in the body? |

Zero-cost metrics (citation, diversity, authority) run by default; the two LLM
metrics are opt-out via flags, so you can trade cost for depth.

## Concept alignment (why this is more than ad-hoc metrics)

The suite maps onto standard evaluation ontologies where they apply, and marks
where autonomous research needs more:

- **Faithfulness / Answer Relevancy** ← align with **RAGAS**. `unsupported_claim`
  even uses the field's standard three-way support scale (supported / inferred /
  unsupported), matching ALCE-style *full / partial / no support*.
- **Citation** ← aligns with **ALCE citation precision** (of the references it
  lists, how many are actually used). Current implementation is *structural*; a
  *semantic* version (does the citation truly support its claim, NLI-style) is on
  the roadmap.
- **Source Quality** ← a deliberate **extension**. RAG-oriented frameworks assume
  the context is *given*, so they have no notion of "source quality". A research
  agent finds its own sources, so authority and diversity of those sources become
  first-class metrics — this is the dimension standard RAG eval can't express.

## Architecture

A thin, dependency-free framework layer (mirrors DeepEval's `BaseMetric` +
test-case design):

```text
base.py        BaseMetric / EvalSample / MetricResult   — abstractions (+ `sources`, the RAG-framework gap)
suite.py       5 metric wrappers + evaluate() entry      — standardized I/O + concept-alignment metadata
metrics.py     raw metric functions                      — pure logic (unit-tested, perturbation-validated)
perturbation.py  behavioral reliability test             — graded degradation, asserts monotonic response
run_eval.py / benchmark.py                                — runners (single query / multi-config comparison)
```

Every metric declares its `group` and the standard concept it `aligned_with`, so
the ontology above is encoded in code, not just docs. `MetricResult.score` is
always *higher = better* (0–1) so results aggregate and compare uniformly.

## Reliability (perturbation-validated)

The metrics aren't just implemented — they're checked for *reliability*.
`perturbation.py` deliberately degrades a report (remove citations, swap to
low-authority sources, corrupt claims) in graded steps and asserts each metric
responds **monotonically**. This surfaced and fixed real defects that mocked unit
tests and final outputs couldn't reveal — e.g. batch LLM scoring was letting one
claim contaminate another's score, fixed by scoring each claim independently.

## Usage

```bash
# Full evaluation (all metrics)
python -m evals.quality_eval.run_eval --num_examples 5

# Zero-cost metrics only
python -m evals.quality_eval.run_eval --num_examples 10 --no-subtopic --no-unsupported-claim

# Reliability check
python -m evals.quality_eval.perturbation

# Compare configs / runs
python -m evals.quality_eval.benchmark --configs single-gpt4o single-gpt4o-mini
python -m evals.quality_eval.benchmark --compare LOG_A LOG_B
```

Programmatic use via the standardized entry point:

```python
from evals.quality_eval.base import EvalSample
from evals.quality_eval.suite import evaluate, default_metrics

sample  = EvalSample(query=q, report=report, sources=urls, context=ctx)
results = await evaluate(sample, default_metrics(), grader_model)
for r in results:
    print(r.group, r.name, r.score)   # typed, tagged, higher = better
```

## Roadmap

- **Semantic citation precision** (does a citation truly support its claim,
  NLI/LLM-judge) → promote the `Citation` group to a full `Precision` family.
- **True answer relevancy** (on-topic-ness), complementing `subtopic_coverage`'s
  completeness view.
- **Component-level evaluation** of the multi-agent pipeline (planner / researcher
  / writer / reviewer) to locate bottlenecks — the natural next phase.

Dependencies: `langchain-openai`, `python-dotenv` (+ `judges` for the optional
hallucination check). Env: `OPENAI_API_KEY`, `TAVILY_API_KEY`.
