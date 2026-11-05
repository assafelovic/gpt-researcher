---
id: tree_quality
version: 5
group: Query quality
used_by: decomposition_tree_quality
---

You are auditing how a research agent split a query into sub-queries before
searching the web. Judge each child query on its own, then the split as a
whole. For every answer, quote the parent or child words it rests on.

Original research question (the root of the whole search tree):
{question}

Path from the original question (0) down to the parent (last line), one query
per level; long queries are cut:
{path}

Parent query:
{parent}

Child queries:
{children}

For EACH child, answer true or false for each of the four checks below.

narrower:
@include query_quality#narrower

searchable:
@include query_quality#searchable

serves_parent:
@include query_quality#serves_parent

serves_question (false when the child has drifted):
@include query_quality#drift
If the parent is the original question itself, give the same answer as
serves_parent.

Then, for the split as a whole, list the distinct aspects of the parent (at
most 6, each a short phrase) and, for each aspect, the numbers of the children
aimed at it (an empty list when no child picks it up).

What counts as an aspect:
@include query_quality#aspect

What counts as aimed at:
@include query_quality#aimed_at

Return ONLY JSON:
{"children": [{"child": 1, "narrower": true, "searchable": true,
                "serves_parent": true, "serves_question": true, "evidence": "..."}],
  "aspects": [{"aspect": "...", "children": [1]}]}
