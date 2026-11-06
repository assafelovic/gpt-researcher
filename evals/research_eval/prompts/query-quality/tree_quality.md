---
id: tree_quality
version: 17
used_by: decomposition_tree_quality
---

# Task: decomposition tree quality

Judge how a research agent split a query into sub-queries before searching
the web. For each child query, decide which steps it takes away from its
parent (wider, deeper, specific: name every one it clearly takes; one is
enough for a good split), or whether it is restated or has drifted. For
every answer, quote the parent or child words it rests on.

In deep mode a split can follow a search step whose findings are listed;
then also say which findings each child builds on. A child builds on a
finding when it asks more about something the finding states: a company,
figure, event, trend or open question it names, in the same or other words,
even when that topic is one of several in the child. Sharing only the broad
subject of the whole search is not enough. Example: after the finding
"Northvolt's Skelleftea plant ran at a third of its capacity in 2024", the
child "why Northvolt Skelleftea capacity use stayed low in 2024" builds on it.
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
