# Judge prompts

Every prompt the evaluator sends to the judge model is a file in this folder,
so they can be read and edited in one place. The code only loads them
(`__init__.py`).

## File format

```
---
id: tree_quality              # same as the file name
version: 4                    # bump on every change of the text
used_by: decomposition_tree_quality
---

The prompt text. {question} is filled in when the prompt is sent.
Other braces, like the JSON the judge must return, are literal.
@include query_quality#narrower      <- replaced by that section of skills/query_quality.md
```

## Editing a prompt

1. Edit the text (or a skill section it includes).
2. Bump `version` in every prompt whose text changed. The version is part of
   every cache key and is recorded with each score, so old verdicts are never
   mixed with new ones.
3. Run `python -m evals.research_eval.prompts --lock` to record the new text
   hash in `versions.json`. `tests/test_research_eval_prompts.py` fails when a
   text changed and its version did not.
4. Rescore: only the prompts with a new version call the judge again.

## Skills

`skills/` holds shared definitions with good and bad examples, one file per
metric group. A prompt pulls in only the sections it needs with
`@include <skill>#<section>`, so a concept is defined once for every metric
that uses it.

## Prompts

| Group | File | Version | Used by | Filled in |
|---|---|---|---|---|
| Query quality | [`key_points.md`](key_points.md) | 1 | key points for the question (key_points.py), decomposition_coverage, material_coverage, query_relevance, comprehensiveness | `question` |
| Query quality | [`decomposition_coverage.md`](decomposition_coverage.md) | 1 | decomposition_coverage | `question`, `key_points`, `subqueries` |
| Query quality | [`subquery_redundancy.md`](subquery_redundancy.md) | 2 | subquery_redundancy | `question`, `queries` |
| Query quality | [`tree_quality.md`](tree_quality.md) | 4 | decomposition_tree_quality | `question`, `path`, `parent`, `children` |
| Source quality | [`domain_authority.md`](domain_authority.md) | 1 | source_authority | `domains` |
| Retrieval quality | [`query_relevance.md`](query_relevance.md) | 3 | query_relevance | `question`, `key_points`, `other_queries`, `query`, `material` |
| Retrieval quality | [`material_coverage.md`](material_coverage.md) | 1 | material_coverage | `question`, `points` |
| Writing quality | [`comprehensiveness.md`](comprehensiveness.md) | 1 | comprehensiveness | `question`, `key_points`, `report` |
| Writing quality | [`quality_rubric.md`](quality_rubric.md) | 1 | insight, readability | `question` |
| Writing quality | [`quality_score.md`](quality_score.md) | 2 | insight, readability | `question`, `criteria`, `report` |
| Writing quality | [`topic_relevance.md`](topic_relevance.md) | 1 | topic_relevance | `question`, `paragraphs` |
| Writing quality | [`toxicity_bias.md`](toxicity_bias.md) | 1 | toxicity, bias | `text` |
| Writing authority | [`paragraph_audit.md`](paragraph_audit.md) | 4 | citation audit (citation_audit.py), source_utilization, citation_recall, citation_precision, effective_citations, faithfulness | `question`, `sentences`, `material` |
| Writing authority | [`claim_recheck.md`](claim_recheck.md) | 3 | citation audit recheck (citation_audit.py) | `question`, `claims`, `material` |
