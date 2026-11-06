---
id: subquery_redundancy
version: 9
used_by: subquery_redundancy
---

# Task: subquery redundancy

## Goal
- Judge whether the agent searched the same thing twice.
- The agent split the core query into queries, and split some of those
  again. You are given every query it searched.

## How the queries are listed
- Numbered in the order they were searched.
- After the number, the queries it was split from are given in brackets, top
  first: "7. [2 > 4]" means query 7 came from query 4, which came from
  query 2.
- A query without brackets came straight from the core query.

## What to decide for each query
- repeats: the number of an EARLIER query (a lower number) that it repeats,
  or null.
- Never compare a query with the queries in its own brackets: they overlap
  by design.
- Query 1 is never a repeat. When a query repeats several earlier ones, give
  the lowest number.
- evidence: quote the words of both queries your answer rests on.

## What counts as a repeat
- This is not the child-parent "restated" check: the two queries compared
  here do not descend from one another.
- A query repeats another only when the same facts would answer both: the
  same information asked in other words ("largest EV battery recycling
  plants in Europe 2025" and "biggest European battery recycling facilities
  by capacity in 2025").
- Shared wording is not enough.
- These are not repeats:
  - a different perspective or source (the Commission's view, industry's
    criticism);
  - a different period, place or group of actors;
  - a different subtopic of the same object (plant capacity, plant costs);
  - one query asking for only a part of the other.

## Answer format
Return ONLY JSON, one entry per query, in order:
{"queries": [{"query": 1, "repeats": null, "evidence": ""},
             {"query": 2, "repeats": 1, "evidence": "..."}]}

@user

Research question:
{question}

Queries:
{queries}
