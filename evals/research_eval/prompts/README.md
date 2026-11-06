# Judge prompts

Every prompt the evaluator sends to the judge model lives here, so they can be
read and edited in one place. The code only loads them (`__init__.py`).

## Layout: one skill per metric group

```
prompts/
├── query-quality/
│   ├── SKILL.md                  what the group judges + its shared definitions
│   ├── tree_quality.md           one file per prompt
│   ├── tree_quality.schema.json  the JSON its answer must be
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
version: 10                   # bump on every change of the text or the schema
used_by: decomposition_tree_quality
---

The task, the definitions and the answer format: the system message, the
same on every call. Braces here, like the JSON example, are literal.
@include query-quality#relation      <- replaced by that section of query-quality/SKILL.md

@user

The data of one call: the user message. {question} is filled in when the
prompt is sent; placeholders may only appear below @user.
```

Each call sends the two parts as a system and a user message, with
`<id>.schema.json` as the answer schema in strict structured-output mode: the
API only returns JSON of that shape, so a reply can no longer be cut off
prose or miss a field. Every object in a schema lists all its properties as
required and allows no others (OpenAI's strict mode); a test checks that, and
that the JSON example in the prompt fits its schema. Set
`EVAL_JUDGE_STRUCTURED=0` for a judge model without structured output.

A group gets its shared sections when it is reviewed in stage 2; until then
its `SKILL.md` names the candidates and its prompts state their definitions
inline.

## Editing a prompt or a skill section

1. Edit the text or the schema. A skill section changes every prompt that
   includes it (the table below lists them). A new answer field goes in both
   the JSON example and the schema.
2. Bump `version` in every prompt whose text or schema changed. The version
   is part of every cache key and, with the text hash, of the scorer version
   recorded with each score, so old verdicts are never mixed with new ones.
   Bump a metric's own version only when its code changes.
3. Run `python -m evals.research_eval.prompts --lock` to record the new text
   hash in `versions.json` (it also rewrites the table below).
   `tests/test_research_eval_prompts.py` fails when a text changed and its
   version did not.
4. Rescore, then rerun the perturbation check and a noise copy for the
   metrics that changed: that is how a prompt change is tested.

## Prompts

<!-- prompts:start (written by --lock) -->
| Group | File | Version | Used by | Skill sections | Filled in | Schema |
|---|---|---|---|---|---|---|
| [query-quality](query-quality/SKILL.md) | [`decomposition_coverage.md`](query-quality/decomposition_coverage.md) | 5 | decomposition_coverage | query-quality#principles, query-quality#aimed_at | `question`, `key_points`, `subqueries` | [json](query-quality/decomposition_coverage.schema.json) |
| [query-quality](query-quality/SKILL.md) | [`key_points.md`](query-quality/key_points.md) | 2 | key points for the question (key_points.py), decomposition_coverage, material_coverage, query_relevance, comprehensiveness | - | `question` | [json](query-quality/key_points.schema.json) |
| [query-quality](query-quality/SKILL.md) | [`subquery_redundancy.md`](query-quality/subquery_redundancy.md) | 6 | subquery_redundancy | query-quality#principles, query-quality#repeat | `question`, `queries` | [json](query-quality/subquery_redundancy.schema.json) |
| [query-quality](query-quality/SKILL.md) | [`tree_quality.md`](query-quality/tree_quality.md) | 10 | decomposition_tree_quality | query-quality#principles, query-quality#relation, query-quality#drift, query-quality#builds_on | `question`, `path`, `parent`, `findings`, `children` | [json](query-quality/tree_quality.schema.json) |
| [source-quality](source-quality/SKILL.md) | [`domain_authority.md`](source-quality/domain_authority.md) | 2 | source_authority | - | `domains` | [json](source-quality/domain_authority.schema.json) |
| [retrieval-quality](retrieval-quality/SKILL.md) | [`material_coverage.md`](retrieval-quality/material_coverage.md) | 2 | material_coverage | - | `question`, `points` | [json](retrieval-quality/material_coverage.schema.json) |
| [retrieval-quality](retrieval-quality/SKILL.md) | [`query_relevance.md`](retrieval-quality/query_relevance.md) | 4 | query_relevance | - | `question`, `key_points`, `other_queries`, `query`, `material` | [json](retrieval-quality/query_relevance.schema.json) |
| [writing-quality](writing-quality/SKILL.md) | [`comprehensiveness.md`](writing-quality/comprehensiveness.md) | 2 | comprehensiveness | - | `question`, `key_points`, `report` | [json](writing-quality/comprehensiveness.schema.json) |
| [writing-quality](writing-quality/SKILL.md) | [`quality_rubric.md`](writing-quality/quality_rubric.md) | 2 | insight, readability | - | `question` | [json](writing-quality/quality_rubric.schema.json) |
| [writing-quality](writing-quality/SKILL.md) | [`quality_score.md`](writing-quality/quality_score.md) | 3 | insight, readability | - | `question`, `criteria`, `report` | [json](writing-quality/quality_score.schema.json) |
| [writing-quality](writing-quality/SKILL.md) | [`topic_relevance.md`](writing-quality/topic_relevance.md) | 2 | topic_relevance | - | `question`, `paragraphs` | [json](writing-quality/topic_relevance.schema.json) |
| [writing-quality](writing-quality/SKILL.md) | [`toxicity_bias.md`](writing-quality/toxicity_bias.md) | 2 | toxicity, bias | - | `text` | [json](writing-quality/toxicity_bias.schema.json) |
| [writing-authority](writing-authority/SKILL.md) | [`claim_recheck.md`](writing-authority/claim_recheck.md) | 4 | citation audit recheck (citation_audit.py) | - | `question`, `claims`, `material` | [json](writing-authority/claim_recheck.schema.json) |
| [writing-authority](writing-authority/SKILL.md) | [`paragraph_audit.md`](writing-authority/paragraph_audit.md) | 5 | citation audit (citation_audit.py), source_utilization, citation_recall, citation_precision, effective_citations, faithfulness | - | `question`, `sentences`, `material` | [json](writing-authority/paragraph_audit.schema.json) |
<!-- prompts:end -->
