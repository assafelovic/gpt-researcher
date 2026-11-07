---
id: subquery_redundancy
version: 12
used_by: subquery_redundancy
---

# Task: subquery redundancy

## Goal
- Judge whether the agent searched the same thing twice.
- You are given two queries the agent searched, A (searched first) and B. Neither was split from the other.

## What counts as a repeat
- B repeats A only when the same facts would answer both: the same information asked in other words ("largest EV battery recycling plants in Europe 2025" and "biggest European battery recycling facilities by capacity in 2025").
- Shared wording is not enough.
- Check what facts each query asks for that the other does not. Wording, word order, a year, synonyms ("top vendors", "leading companies") and the example names in a list ("including CATL, BYD, LG") are not facts asked for: when only they differ, it is a repeat. Long keyword queries that list the same topics in another order are repeats.
- Different names make a different query only when the query is about those named actors themselves ("CATL's recycling plants" and "BYD's recycling plants").
- These are not repeats:
  - a different perspective or source (the Commission's view, industry's criticism);
  - a different period or place, or a different type of actor (banks and insurers; the EU and the US);
  - a different subtopic of the same object (plant capacity, plant costs);
  - one query asking for only a part of the other.

## Answer format
Fill the fields in this order:
- only_in_a: the facts A asks for that B does not ("nothing" if only wording, synonyms or example names differ);
- only_in_b: the facts B asks for that A does not (the same);
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
