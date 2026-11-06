---
name: query-quality
description: How the judge rates the queries a research agent searched before writing (which key points the sub-queries reach, whether they repeat each other, whether each split goes deeper than its parent or drifts). Shared by the prompts of decomposition_coverage, subquery_redundancy and decomposition_tree_quality.
---

# Query quality

This group judges the search plan, not the report: the queries the agent
searched and how each one was split into sub-queries. Breadth (does the plan
reach every key point of the question) is decomposition_coverage, waste (do
queries repeat each other) is subquery_redundancy, and depth (does each split
go below its parent rather than restate or leave it) is
decomposition_tree_quality. Every prompt in this
folder includes the sections it needs with `@include query-quality#<section>`.
The text under a `## <section>` heading is sent to the judge as it is, so it
is written for the judge; this introduction is not sent.

Why the sections are short: the judge reads them on every call, and a long
list of special cases makes it match examples instead of applying the rule.
Each section gives the rule, the reason when it is not obvious, and at most
one example. The examples are about EV batteries, a topic outside the
evaluation questions, so the judge learns the rule rather than the answer.

Editing a section changes every prompt that includes it (see the table in
../README.md): bump those prompts' versions, then run
`python -m evals.research_eval.prompts --lock`.

key_points.md does not include these sections: the question's key points are
frozen in the dataset, and changing that prompt would not regenerate them.

## principles

How to judge:
- Judge only what you are shown: the queries and, where given, the key
  points or findings. Do not guess what the agent meant or what else the
  search returned.
- Rest each answer on words you can quote from what you are shown.
- These answers are counted and compared across runs, so the same queries
  must get the same answer every time. In a borderline case, apply the
  definition as written and pick the answer that needs fewer assumptions.

## aimed_at

A query is aimed at an aspect when it names the aspect or is plainly written
to find out about it. Sharing broad topic words is not enough: "EV battery
supply in Europe" is not aimed at "battery recycling".

## relation

Give each child one relation. First rule out the two failures:
- drifted: it no longer helps answer the parent or the original research
  question (see drift).
- restated: the same facts would answer the child and the whole parent.
  Rewording, reordering, dropping words, or listing names the parent already
  covers does not change that.
Otherwise give the one of these that best describes what the child mainly asks:
- deeper: why something in the parent happens or what it leads to: its
  causes, effects, drivers, mechanisms or trade-offs. Asking for a source,
  agency, rule text, data field, example, case study, size tier or period
  is specific, not deeper, even when worded as "how"; so is a section
  heading such as "profile of the leading vendors".
- extension: an angle the parent does not name but that helps answer it,
  such as another actor, a side effect or a comparison.
- specific: a narrower part of the parent's own question at the same level:
  one named actor, place, period, product or figure the parent does not
  already pin down, or one of several topics the parent lists.
Example, for the parent "EU battery recycling rules 2025": "why lithium
recovery in EU recycling plants stays below the targets" is deeper; "how the
rules change battery import costs for carmakers" is an extension; "recycling
quotas each EU country met in 2025" is specific; "2025 EU rules for recycling
batteries" is restated; "best electric cars to buy in 2025" has drifted.

## drift

A child has drifted when it no longer serves the original research question,
even if it serves its parent. Drift builds up one step at a time in deep
trees, so read the path from the question down to the parent.
Example: question "How are European EV makers securing battery materials?",
path "Northvolt financing" > "Northvolt bond terms": the child "Swedish
insolvency law for bondholders" has drifted.

## builds_on

A child builds on a finding when it asks more about something a listed
finding states: a company, figure, event, trend or open question it names,
in the same or other words. Count it even when that topic is one of several
in the child. Sharing only the broad subject of the whole search is not
enough.
Example: after the finding "Northvolt's Skelleftea plant ran at a third of
its capacity in 2024", the child "why Northvolt Skelleftea capacity use stayed
low in 2024" builds on it.

## repeat

A query repeats another only when the same facts would answer both: the same
information asked in other words ("largest EV battery recycling plants in
Europe 2025" and "biggest European battery recycling facilities by capacity
in 2025"). Shared wording is not enough. These are not repeats:
- a different perspective or source (the Commission's view, industry's
  criticism);
- a different period, place or group of actors;
- a different subtopic of the same object (plant capacity, plant costs);
- one query asking for only a part of the other.
