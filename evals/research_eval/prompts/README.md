# Judge prompts

Every prompt the evaluator sends to the judge model lives here, so they can be
read and edited in one place. The code only loads them (`__init__.py`).

## Layout: one skill per metric group

```
prompts/
├── query-quality/
│   ├── SKILL.md                  what the group judges + its shared definitions
│   ├── tree_quality.md           one file per prompt
│   └── ...
├── source-quality/
├── retrieval-quality/
├── writing-quality/
├── writing-authority/
└── versions.json                 each prompt's version and text hash
```

Each group's `SKILL.md` follows the skill layout: a header with `name` and
`description`, then a short introduction for maintainers (not sent to the
judge), then one `## <section>` per shared definition. The text of a section
runs to the next heading and is sent to the judge as it is, so it is written
for the judge: the rule, the reason when it is not obvious, and at most one
example. A prompt pulls in only the sections it needs:

```
---
id: tree_quality              # same as the file name, unique across groups
version: 7                    # bump on every change of the text
used_by: decomposition_tree_quality
---

The prompt text. {question} is filled in when the prompt is sent.
Other braces, like the JSON the judge must return, are literal.
@include query-quality#narrower      <- replaced by that section of query-quality/SKILL.md
```

A group gets its shared sections when it is reviewed in stage 2; until then
its `SKILL.md` names the candidates and its prompts state their definitions
inline.

## Editing a prompt or a skill section

1. Edit the text. A skill section changes every prompt that includes it (the
   table below lists them).
2. Bump `version` in every prompt whose text changed. The version is part of
   every cache key and is recorded with each score, so old verdicts are never
   mixed with new ones. Bump the metric's version too.
3. Run `python -m evals.research_eval.prompts --lock` to record the new text
   hash in `versions.json` (it also rewrites the table below).
   `tests/test_research_eval_prompts.py` fails when a text changed and its
   version did not.
4. Rescore, then rerun the perturbation check and a noise copy for the
   metrics that changed: that is how a prompt change is tested.

## Prompts

<!-- prompts:start (written by --lock) -->
| Group | File | Version | Used by | Skill sections | Filled in |
|---|---|---|---|---|---|
| [query-quality](query-quality/SKILL.md) | [`decomposition_coverage.md`](query-quality/decomposition_coverage.md) | 3 | decomposition_coverage | query-quality#principles, query-quality#aimed_at | `question`, `key_points`, `subqueries` |
| [query-quality](query-quality/SKILL.md) | [`key_points.md`](query-quality/key_points.md) | 1 | key points for the question (key_points.py), decomposition_coverage, material_coverage, query_relevance, comprehensiveness | - | `question` |
| [query-quality](query-quality/SKILL.md) | [`parent_aspects.md`](query-quality/parent_aspects.md) | 2 | decomposition_tree_quality | query-quality#principles, query-quality#aspect | `question`, `parent` |
| [query-quality](query-quality/SKILL.md) | [`subquery_redundancy.md`](query-quality/subquery_redundancy.md) | 4 | subquery_redundancy | query-quality#principles, query-quality#repeat | `question`, `queries` |
| [query-quality](query-quality/SKILL.md) | [`tree_quality.md`](query-quality/tree_quality.md) | 7 | decomposition_tree_quality | query-quality#principles, query-quality#narrower, query-quality#searchable, query-quality#serves_parent, query-quality#drift, query-quality#aimed_at | `question`, `path`, `parent`, `children`, `aspects` |
| [source-quality](source-quality/SKILL.md) | [`domain_authority.md`](source-quality/domain_authority.md) | 1 | source_authority | - | `domains` |
| [retrieval-quality](retrieval-quality/SKILL.md) | [`material_coverage.md`](retrieval-quality/material_coverage.md) | 1 | material_coverage | - | `question`, `points` |
| [retrieval-quality](retrieval-quality/SKILL.md) | [`query_relevance.md`](retrieval-quality/query_relevance.md) | 3 | query_relevance | - | `question`, `key_points`, `other_queries`, `query`, `material` |
| [writing-quality](writing-quality/SKILL.md) | [`comprehensiveness.md`](writing-quality/comprehensiveness.md) | 1 | comprehensiveness | - | `question`, `key_points`, `report` |
| [writing-quality](writing-quality/SKILL.md) | [`quality_rubric.md`](writing-quality/quality_rubric.md) | 1 | insight, readability | - | `question` |
| [writing-quality](writing-quality/SKILL.md) | [`quality_score.md`](writing-quality/quality_score.md) | 2 | insight, readability | - | `question`, `criteria`, `report` |
| [writing-quality](writing-quality/SKILL.md) | [`topic_relevance.md`](writing-quality/topic_relevance.md) | 1 | topic_relevance | - | `question`, `paragraphs` |
| [writing-quality](writing-quality/SKILL.md) | [`toxicity_bias.md`](writing-quality/toxicity_bias.md) | 1 | toxicity, bias | - | `text` |
| [writing-authority](writing-authority/SKILL.md) | [`claim_recheck.md`](writing-authority/claim_recheck.md) | 3 | citation audit recheck (citation_audit.py) | - | `question`, `claims`, `material` |
| [writing-authority](writing-authority/SKILL.md) | [`paragraph_audit.md`](writing-authority/paragraph_audit.md) | 4 | citation audit (citation_audit.py), source_utilization, citation_recall, citation_precision, effective_citations, faithfulness | - | `question`, `sentences`, `material` |
<!-- prompts:end -->
