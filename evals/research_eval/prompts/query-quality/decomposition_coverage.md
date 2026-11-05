---
id: decomposition_coverage
version: 5
used_by: decomposition_coverage
---

You are auditing which aspects of a research question a research agent decided
to search for. Below are the question's key points and the sub-queries the
agent searched. For EACH key point, list the numbers of the sub-queries that
are aimed at it. A sub-query may serve several key points. Quote the words of
the sub-query your answer rests on; leave the list empty when no sub-query
targets the point.

@include query-quality#principles

What counts as aimed at:
@include query-quality#aimed_at

Return ONLY JSON, one entry per key point, in order:
{"points": [{"point": 1, "evidence": "...", "subqueries": [2]}]}

@user

Question:
{question}

Key points:
{key_points}

Sub-queries:
{subqueries}
