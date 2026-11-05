---
name: query-quality
description: How the judge rates the queries a research agent searched before writing (how it split the question, which aspects the sub-queries reach, whether they repeat or drift). Shared by the prompts of decomposition_coverage, subquery_redundancy and decomposition_tree_quality.
---

# Query quality

This group judges the search plan, not the report: the queries the agent
searched and how each one was split into sub-queries. Every prompt in this
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
- Judge the words of the queries only. Do not guess what the agent meant or
  what the search returned.
- Rest each answer on words you can quote from the queries.
- These answers are counted and compared across runs, so the same queries
  must get the same answer every time. In a borderline case, apply the
  definition as written and pick the answer that needs fewer assumptions.

## aspect

An aspect is one distinct part of what a query asks: something a good answer
would treat in its own paragraph. Take aspects from the query's own words and
scope (its place, period, actors and object). An aspect is smaller than the
whole query and larger than a single fact; leave out what the query does not
ask and parts every answer has, such as background.
Example: "How are European EV makers securing battery materials since 2023?"
has the aspects supply contracts, stakes in mines and refiners, recycling, and
EU policy support; not "history of electric cars" (not asked) or "lithium
price on 1 March 2024" (a single fact).

## aimed_at

A query is aimed at an aspect when it names the aspect or is plainly written
to find out about it. Sharing broad topic words is not enough: "EV battery
supply in Europe" is not aimed at "battery recycling".

## narrower

A child is narrower when it asks for one part of its parent, or a more
concrete angle on it: a named actor, place, period, measure or source. A child
that restates the whole parent is not narrower, even with a few words added,
dropped or reordered.
Example: for the parent "EU battery material supply risks 2024 2025", "EU
dependence on Chinese graphite for anodes" is narrower; "2024 2025 EU supply
risks for battery materials and policy response" is not.

## searchable

A child is searchable when, pasted into a web search engine as it is, it would
return focused results about one thing. It is not when it is too vague
("battery news"), or when it piles up terms about several things that no
single page covers. A long query is fine when every term narrows the same
thing.

## serves_parent

A child serves its parent when what it asks helps answer the parent. A
moderate step beyond the parent's literal scope still counts (for a parent on
EU battery rules, how Germany enforces them); a child on another question does
not ("best electric cars to buy in 2025").

## drift

A child has drifted when it no longer serves the original research question,
even if it serves its parent. Drift builds up one step at a time in deep
trees, so read the path from the question down to the parent.
Example: question "How are European EV makers securing battery materials?",
path "Northvolt financing" > "Northvolt bond terms": the child "Swedish
insolvency law for bondholders" has drifted.

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
