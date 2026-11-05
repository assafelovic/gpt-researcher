# Query quality

Shared definitions for the judge prompts of the query-quality metrics:
`decomposition_coverage`, `subquery_redundancy` and `decomposition_tree_quality`.
Each prompt pulls in only the sections it needs with
`@include query_quality#<section>`; the text under a `## section` heading is
copied into the prompt as it is, so write it to be read by the judge.

The examples are about topics outside the evaluation questions on purpose:
the judge should learn the rule, not the answer for a run it is scoring.

Editing a section changes every prompt that includes it: bump those prompts'
versions (see ../README.md).

## aspect

An aspect is one distinct part of what a query asks, one that a good answer
would treat in its own paragraph or section.
- Take aspects from the query's own words and scope: its place, period,
  actors and object. Do not add aspects the query does not ask for.
- An aspect is one thing to find out: smaller than the whole query, larger
  than a single fact.
- Leave out parts every answer has, such as background, introduction or
  conclusion.
Example. Query: "How are European EV makers securing battery materials since
2023?" Aspects: long-term supply contracts; stakes in mines and refiners;
battery recycling; EU policy support. Not aspects: "history of electric
vehicles" (not asked), "lithium price on 1 March 2024" (a single fact),
"battery materials in Europe" (the whole query again).

## aimed_at

A query is aimed at an aspect when it names that aspect, or is clearly
written to find information about it. Sharing broad topic words is not
enough: "EV battery supply in Europe" is not aimed at "battery recycling"
just because recycling is part of supply.

## narrower

A child is narrower when it asks for one part of its parent, or a more
concrete angle on it: a named actor, place, period, measure or source.
It is not narrower when it restates the whole parent in other words, even
with a few terms added, dropped or reordered.
- Narrower. Parent: "EU battery material supply risks 2024 2025". Child:
  "EU dependence on Chinese graphite for battery anodes 2024 2025".
- Not narrower. Parent: "EU battery material supply risks 2024 2025 lithium
  cobalt nickel graphite". Child: "2024 2025 EU supply risks for lithium
  nickel cobalt and graphite battery materials and policy response".

## searchable

A child is searchable when, pasted into a web search engine as it is, it
would return focused results about one thing.
- Not searchable when it is too vague ("battery news", "EV overview").
- Not searchable when it piles up terms about several different things that
  no single page answers ("EU raw materials act graphite tariffs recycling
  targets Northvolt bankruptcy sodium-ion US tax credits 2025").
- A long query is fine when every term narrows the same thing ("Northvolt
  Skelleftea plant battery output 2024 annual report").

## serves_parent

A child serves its parent when what it asks helps answer the parent.
Moderate extension beyond the parent's literal scope counts when it helps
answer it: for a parent on EU battery rules, a child on how Germany enforces
them serves it. A child on another question does not: for the same parent,
"best electric cars to buy in 2025".

## drift

A child has drifted when it no longer serves the original research question,
even if it serves its parent. Drift builds up step by step in deep trees.
Research question: "How are European EV makers securing battery materials?"
Path: "Northvolt financing" -> "Northvolt 2024 bond terms and creditors" ->
child "Swedish insolvency law for bondholders". The child serves its parent
but has left the research question. Use the path from the research question
down to the parent to see how far a branch has already moved.

## repeat

A query repeats another ONLY when both ask for the same information in other
words, so that the same facts would answer both. Example of a repeat:
"largest EV battery recycling plants in Europe 2025" and "biggest European
battery recycling facilities by capacity in 2025".
These are NOT repeats, even when the wording overlaps heavily:
- a different perspective, or a different source or authority ("EU
  Commission view on battery recycling targets" and "industry criticism of
  EU battery recycling targets");
- a different time period, place, or group of actors ("battery recycling
  capacity in Germany" and "battery recycling capacity in France");
- a separate subtopic about the same object ("recycling plant capacity" and
  "recycling plant costs");
- a narrower query that asks for only one part of a broader query ("EU
  battery recycling targets and plants" and "EU battery recycling targets").
