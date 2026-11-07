---
id: material_coverage
version: 3
used_by: material_coverage
---

# Task: material coverage

## Goal
- Judge which key points the retrieved material covers, before any report
  is written.
- You are given the core query and, under each numbered key point, the
  retrieved passages that match it best, picked by word overlap.

## What to decide for each key point
- passages: the ids of the passages your answer rests on, from under any
  key point. Empty for "none".
- evidence: quote the words of those passages that give the information.
- coverage: "full", "partial" or "none", by the definitions above.

## Covered or not
- A passage is shown under the point it matches best, but it may cover
  another point too: use every passage shown.
- Sharing the point's words is not enough: the passage must give
  information on the point itself.
- Naming an example that belongs to the point (a company, a place, a
  product) does not cover it unless the passage says something about the
  point.
- If your evidence has to say the passages do not give information on the
  point, the coverage is "none".

## Answer format
Return ONLY JSON, one entry per key point, in order:
{"points": [{"point": 1, "passages": ["1a"], "evidence": "...", "coverage": "full"}]}

@user

Question:
{question}

{points}
