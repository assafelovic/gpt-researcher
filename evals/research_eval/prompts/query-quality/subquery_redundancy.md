---
id: subquery_redundancy
version: 11
used_by: subquery_redundancy
---

# Task: subquery redundancy

## Goal
- Judge whether the agent searched the same thing twice.
- You are given two queries the agent searched, A (searched first) and B. Neither was split from the other.

## What counts as a repeat
- B repeats A only when the same facts would answer both: the same information asked in other words ("largest EV battery recycling plants in Europe 2025" and "biggest European battery recycling facilities by capacity in 2025").
- Shared wording is not enough.
- Check what each query asks that the other does not. When that is only wording, word order, a year or a list of names, it is a repeat. Long keyword queries that list the same topics in another order are repeats.
- These are not repeats:
  - a different perspective or source (the Commission's view, industry's criticism);
  - a different period, place or group of actors;
  - a different subtopic of the same object (plant capacity, plant costs);
  - one query asking for only a part of the other.

## Answer format
Fill the fields in this order:
- only_in_a: what A asks that B does not ("nothing" if so);
- only_in_b: what B asks that A does not ("nothing" if so);
- repeat: true or false.
Return ONLY JSON:
{"only_in_a": "...", "only_in_b": "...", "repeat": false}

@user

Research question:
{question}

Query A:
{query_a}

Query B:
{query_b}
