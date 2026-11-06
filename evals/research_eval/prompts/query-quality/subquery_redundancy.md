---
id: subquery_redundancy
version: 7
used_by: subquery_redundancy
---

# Task: subquery redundancy

Judge whether the agent searched the same thing twice. The agent split the
core query into queries, and split some of those again. Below is every
query it searched, numbered in the order they were searched. After the number,
the queries it was split from are given in brackets, top first: "7. [2 > 4]"
means query 7 came from query 4, which came from query 2. A query without
brackets came straight from the research question.

For EACH query, say whether it repeats an EARLIER query (a lower number) that
is not in its own brackets. A query and the queries it was split from overlap
by design and are never compared.

This is not the child-parent "restated" check: here two queries are
compared that do not descend from one another. A query repeats another only
when the same facts would answer both: the same information asked in other
words ("largest EV battery recycling plants in Europe 2025" and "biggest
European battery recycling facilities by capacity in 2025"). Shared wording
is not enough. These are not repeats:
- a different perspective or source (the Commission's view, industry's
  criticism);
- a different period, place or group of actors;
- a different subtopic of the same object (plant capacity, plant costs);
- one query asking for only a part of the other.

Query 1 is never a repeat. When a query repeats several earlier ones, give the
lowest number. Quote the words of both queries your answer rests on.

Return ONLY JSON, one entry per query, in order; "repeats" is the number of
the earlier query it repeats, or null:
{"queries": [{"query": 1, "repeats": null, "evidence": ""},
             {"query": 2, "repeats": 1, "evidence": "..."}]}

@user

Research question:
{question}

Queries:
{queries}
