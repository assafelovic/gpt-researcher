---
id: decomposition_coverage
version: 10
used_by: decomposition_coverage
---

# Task: decomposition coverage

## Goal
- Judge which key points of the core query the agent decided to search for.
- You are given the core query, its key points and the sub-queries the agent
  searched.
- Under a key point, "includes" lists the sub-points a good answer gives on
  it. A sub-query aimed at one of them is aimed at the point.

## What to decide for each key point
- subqueries: the numbers of the sub-queries aimed at it. A sub-query may
  serve several key points. Leave the list empty when no sub-query targets
  the point.
- evidence: quote the words of the sub-query your answer rests on.

## Aimed at
- A sub-query is aimed at a key point when it names the point or is plainly
  written to find out about it.
- Sharing broad topic words is not enough: "EV battery supply in Europe" is
  not aimed at "battery recycling".
- Naming an example that belongs to the point (a company, a place, a
  product) does not aim the sub-query at it unless it asks about the point.
- If your evidence has to say the sub-query does not ask about the point,
  leave it out.

## Answer format
Return ONLY JSON, one entry per key point, in order:
{"points": [{"point": 1, "evidence": "...", "subqueries": [2]}]}

@user

Question:
{question}

Key points:
{key_points}

Sub-queries:
{subqueries}
