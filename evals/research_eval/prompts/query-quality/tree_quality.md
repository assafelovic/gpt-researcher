---
id: tree_quality
version: 8
used_by: decomposition_tree_quality
---

You are auditing how a research agent split a query into sub-queries before
searching the web. Judge each child query on its own, then which aspects of
the parent the children pick up. For every answer, quote the parent or child
words it rests on.

@include query-quality#principles

For EACH child, answer true or false for each of the four checks below.

narrower:
@include query-quality#narrower

searchable:
@include query-quality#searchable

serves_parent:
@include query-quality#serves_parent

serves_question (false when the child has drifted):
@include query-quality#drift
If the parent is the original question itself, give the same answer as
serves_parent.

Then, for EACH aspect of the parent listed below, give the numbers of the
children aimed at it (an empty list when no child picks it up). The aspects
were listed from the parent alone, before its children were known.

What counts as aimed at:
@include query-quality#aimed_at

Return ONLY JSON:
{"children": [{"child": 1, "narrower": true, "searchable": true,
                "serves_parent": true, "serves_question": true, "evidence": "..."}],
  "aspects": [{"aspect": 1, "children": [1]}]}

@user

Original research question (the root of the whole search tree):
{question}

Path from the original question (0) down to the parent (last line), one query
per level; long queries are cut:
{path}

Parent query:
{parent}

Child queries:
{children}

Aspects of the parent:
{aspects}
