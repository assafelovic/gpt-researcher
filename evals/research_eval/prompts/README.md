# Judge prompts

Every prompt the evaluator sends to the judge model lives here, so they can be
read and edited in one place. The code only loads them (`__init__.py`).

## Layout: one skill per metric group

```
prompts/
├── query-quality/
│   ├── SKILL.md                  the group's system prompt (or its shared sections)
│   ├── tree_quality.md           one file per prompt
│   ├── tree_quality.schema.json  the JSON its answer must be
│   └── ...
├── source-quality/
├── retrieval-quality/
├── writing-quality/
├── writing-authority/
└── versions.json                 each prompt's version and text hash
```

Each group's `SKILL.md` has a header with `name` and `description`. There
are two ways a group uses it:

- **Whole skill as system prompt** (`system_prompt: true` in the header; so
  far query-quality and source-quality). The skill is the group's system prompt: background,
  definitions, principles, instructions and suggested steps, written for the
  judge. Every prompt in the folder is sent as that skill followed by its own
  task, its own definitions and its answer format. Maintainers' notes go in
  `<!-- ... -->` comments, which are never sent. A prompt that must not get
  the skill says `skill: none` (key_points: its answers are frozen in the
  dataset).
- **Sections** (the other groups, until they are reviewed). A short
  introduction for maintainers, then one `## <section>` per shared
  definition; a prompt pulls one in with `@include <group>#<section>`.

```
---
id: tree_quality              # same as the file name, unique across groups
version: 20                   # bump on every change of the text or the schema
used_by: decomposition_tree_quality
---

                              <- the whole query-quality/SKILL.md comes first
# Task: decomposition tree quality
The task of this metric, its own definitions and the answer format: the
rest of the system message, the same on every call. Braces here, like the
JSON example, are literal.

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

1. Edit the text or the schema. A whole-skill SKILL.md changes every prompt
   in its folder (except `skill: none`); a skill section changes every prompt
   that includes it (the table below lists them). A new answer field goes in both
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
| [query-quality](query-quality/SKILL.md) | [`decomposition_coverage.md`](query-quality/decomposition_coverage.md) | 9 | decomposition_coverage | query-quality (whole skill) | `question`, `key_points`, `subqueries` | [json](query-quality/decomposition_coverage.schema.json) |
| [query-quality](query-quality/SKILL.md) | [`key_points.md`](query-quality/key_points.md) | 2 | key points for the question (key_points.py), decomposition_coverage, material_coverage, query_relevance, comprehensiveness | - | `question` | [json](query-quality/key_points.schema.json) |
| [query-quality](query-quality/SKILL.md) | [`subquery_redundancy.md`](query-quality/subquery_redundancy.md) | 14 | subquery_redundancy | query-quality (whole skill) | `question`, `query_a`, `query_b` | [json](query-quality/subquery_redundancy.schema.json) |
| [query-quality](query-quality/SKILL.md) | [`tree_quality.md`](query-quality/tree_quality.md) | 20 | decomposition_tree_quality | query-quality (whole skill) | `question`, `path`, `parent`, `findings`, `children` | [json](query-quality/tree_quality.schema.json) |
| [source-quality](source-quality/SKILL.md) | [`domain_authority.md`](source-quality/domain_authority.md) | 6 | source_authority | source-quality (whole skill) | `question`, `domains` | [json](source-quality/domain_authority.schema.json) |
| [retrieval-quality](retrieval-quality/SKILL.md) | [`material_coverage.md`](retrieval-quality/material_coverage.md) | 2 | material_coverage | - | `question`, `points` | [json](retrieval-quality/material_coverage.schema.json) |
| [retrieval-quality](retrieval-quality/SKILL.md) | [`query_relevance.md`](retrieval-quality/query_relevance.md) | 12 | query_relevance | retrieval-quality (whole skill) | `question`, `query`, `material` | [json](retrieval-quality/query_relevance.schema.json) |
| [writing-quality](writing-quality/SKILL.md) | [`comprehensiveness.md`](writing-quality/comprehensiveness.md) | 5 | comprehensiveness | writing-quality (whole skill) | `question`, `key_points`, `report` | [json](writing-quality/comprehensiveness.schema.json) |
| [writing-quality](writing-quality/SKILL.md) | [`quality_rubric.md`](writing-quality/quality_rubric.md) | 4 | insight, readability | writing-quality (whole skill) | `question` | [json](writing-quality/quality_rubric.schema.json) |
| [writing-quality](writing-quality/SKILL.md) | [`quality_score.md`](writing-quality/quality_score.md) | 6 | insight, readability | writing-quality (whole skill) | `question`, `criteria`, `report` | [json](writing-quality/quality_score.schema.json) |
| [writing-quality](writing-quality/SKILL.md) | [`topic_relevance.md`](writing-quality/topic_relevance.md) | 7 | topic_relevance | writing-quality (whole skill) | `question`, `paragraphs` | [json](writing-quality/topic_relevance.schema.json) |
| [writing-quality](writing-quality/SKILL.md) | [`toxicity_bias.md`](writing-quality/toxicity_bias.md) | 4 | toxicity, bias | writing-quality (whole skill) | `text` | [json](writing-quality/toxicity_bias.schema.json) |
| [writing-authority](writing-authority/SKILL.md) | [`claim_recheck.md`](writing-authority/claim_recheck.md) | 7 | citation audit recheck (citation_audit.py) | writing-authority (whole skill) | `question`, `claims`, `material` | [json](writing-authority/claim_recheck.schema.json) |
| [writing-authority](writing-authority/SKILL.md) | [`paragraph_audit.md`](writing-authority/paragraph_audit.md) | 8 | citation audit (citation_audit.py), source_utilization, citation_recall, citation_precision, effective_citations, faithfulness | writing-authority (whole skill) | `question`, `sentences`, `material` | [json](writing-authority/paragraph_audit.schema.json) |
<!-- prompts:end -->
