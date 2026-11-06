---
id: tree_quality
version: 10
used_by: decomposition_tree_quality
---

You are auditing how a research agent split a query into sub-queries before
searching the web. For each child query, decide how it relates to its parent:
whether it goes deeper than the parent, or only restates it or drifts away.
In deep research a split can follow a search step whose findings are listed;
then also say which findings each child follows up. For every answer, quote
the parent or child words it rests on.

@include query-quality#principles

How a child relates to its parent:
@include query-quality#relation

What counts as drift:
@include query-quality#drift

What counts as building on a finding:
@include query-quality#builds_on
Give the numbers of the findings a child builds on, or an empty list. When no
findings are listed, the list is empty for every child.

Return ONLY JSON, one entry per child, in order:
{"children": [{"child": 1, "evidence": "...", "relation": "deeper", "builds_on": []}]}

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
