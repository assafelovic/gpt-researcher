---
id: tree_quality
version: 21
used_by: decomposition_tree_quality
---

# Task: decomposition tree quality

## Goal
- Judge how a research agent split a query into sub-queries before searching
  the web.
- You are given the core query, the path from it down to the parent, the
  parent, its child queries and, in deep mode, the findings of the search
  step the split follows.

## What to decide for each child
- left_out: what the parent asks that the child does not: the topics,
  questions, actors, periods, etc. it lists that the child drops. Write
  "nothing" when the child keeps all of them.
- problem: "restated" or "drifted" when the child takes no step away from
  its parent; otherwise "none".
- directions: every step the child clearly takes: "wider", "deeper",
  "specific". One is enough for a good split. Leave it empty when the
  problem is not "none".
- evidence: quote the parent or child words your answer rests on.
- builds_on: the numbers of the findings the child follows up, or an empty
  list. When no findings are listed, it is empty for every child.

## Restated or specific
- Decide this from left_out, not from the words the two queries share.
- Restated: left_out is "nothing", or only wording, a year or scope the
  parent implies, or names its answer would give.
- Specific: left_out names a whole topic or question the parent lists, so
  the child asks only part of the parent. This holds even when the child
  repeats that part's words, for example when a deep-mode parent lists
  several questions and the child takes one of them.

## Building on a finding (deep mode)
- A child builds on a finding when it asks more about something the finding
  states: a company, figure, event, trend, open question, etc. it names, in the
  same or other words.
- Count it even when that topic is one of several in the child.
- Sharing only the broad subject of the whole search is not enough.
- Example: after the finding "Northvolt's Skelleftea plant ran at a third of
  its capacity in 2024", the child "why Northvolt Skelleftea capacity use
  stayed low in 2024" builds on it.

## Answer format
Return ONLY JSON, one entry per child, in order:
{"children": [{"child": 1, "left_out": "...", "evidence": "...", "problem": "none", "directions": ["deeper"], "builds_on": []}]}

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
