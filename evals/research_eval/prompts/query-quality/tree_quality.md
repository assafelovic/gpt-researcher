---
id: tree_quality
version: 14
used_by: decomposition_tree_quality
---

You are auditing how a research agent split a query into sub-queries before
searching the web. For each child query, decide which steps it takes away
from its parent (deeper, wider, more specific), or whether it only restates
the parent or drifts away.
In deep research a split can follow a search step whose findings are listed;
then also say which findings each child follows up. For every answer, quote
the parent or child words it rests on.

@include query-quality#principles

The steps a child can take:
@include query-quality#steps

What counts as drift:
@include query-quality#drift

What counts as building on a finding:
@include query-quality#builds_on
Give the numbers of the findings a child builds on, or an empty list. When no
findings are listed, the list is empty for every child.

problem is "restated" or "drifted" when the child takes no step, and then
directions is empty; otherwise problem is "none" and directions names at
least one step.

Return ONLY JSON, one entry per child, in order:
{"children": [{"child": 1, "evidence": "...", "problem": "none", "directions": ["deeper"], "builds_on": []}]}

@user

Original research question (the root of the whole search tree):
{question}

Path from the original question (0) down to the parent (last line), one query
per level; long queries are cut:
{path}

Parent query:
{parent}

Findings of the search step this split follows:
{findings}

Child queries:
{children}
