---
id: decomposition_coverage
version: 1
used_by: decomposition_coverage
---

You are auditing which aspects of a research question a research agent decided
to search for. Below are the question's key points and the sub-queries the
agent searched. For EACH key point, list the numbers of the sub-queries that
are aimed at it: the sub-query names that aspect, or is clearly written to
find information about it. A sub-query that only shares broad topic words
(e.g. "crypto regulation in Europe") does not count. A sub-query may serve
several key points. Quote the words of the sub-query your answer rests on;
leave the list empty when no sub-query targets the point.

Question:
{question}

Key points:
{key_points}

Sub-queries:
{subqueries}

Return ONLY JSON, one entry per key point, in order:
{"points": [{"point": 1, "evidence": "...", "subqueries": [2]}]}
