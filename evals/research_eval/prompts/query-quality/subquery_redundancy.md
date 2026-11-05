---
id: subquery_redundancy
version: 6
used_by: subquery_redundancy
---

You are auditing the search plan of a research agent. The agent split the
research question into queries, and split some of those again. Below is every
query it searched, numbered in the order they were searched. After the number,
the queries it was split from are given in brackets, top first: "7. [2 > 4]"
means query 7 came from query 4, which came from query 2. A query without
brackets came straight from the research question.

For EACH query, say whether it repeats an EARLIER query (a lower number) that
is not in its own brackets. A query and the queries it was split from overlap
by design and are never compared.

@include query-quality#principles

What counts as a repeat:
@include query-quality#repeat

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
