---
id: decomposition_coverage
version: 6
used_by: decomposition_coverage
---

# Task: decomposition coverage

Judge which key points of the core query the agent decided to search for.
You are given the key points and the sub-queries the agent searched. For EACH key point, list the numbers of the sub-queries that
are aimed at it. A sub-query may serve several key points. Quote the words of
the sub-query your answer rests on; leave the list empty when no sub-query
targets the point.

A sub-query is aimed at a key point when it names the point or is plainly
written to find out about it. Sharing broad topic words is not enough: "EV
battery supply in Europe" is not aimed at "battery recycling".

Return ONLY JSON, one entry per key point, in order:
{"points": [{"point": 1, "evidence": "...", "subqueries": [2]}]}

@user

Question:
{question}

Key points:
{key_points}

Sub-queries:
{subqueries}
