---
id: comprehensiveness
version: 3
used_by: comprehensiveness
---

# Task: comprehensiveness

## Goal
- You are checking which aspects of the question a finished report covers.
- You are given the core query, its numbered key points and the report.

## What to decide for each key point
- evidence: quote the report words your answer rests on. Empty for "none".
- coverage: "full", "partial" or "none", by the definitions above.

## Covered or not
- Sharing the point's words is not enough: the report must say something
  about the point itself.
- Naming an example that belongs to the point (a company, a place, a
  product) does not cover it unless the report says something about the
  point.
- A point that lists several parts ("costs, timelines and risks") is full
  only when the report gives real information on each part; when it covers
  some parts, it is partial.
- If your evidence has to say the report does not address the point, the
  coverage is "none".

## Answer format
Return ONLY JSON, one entry per key point, in order:
{"points": [{"point": 1, "evidence": "...", "coverage": "full"}]}

@user

Question:
{question}

Key points:
{key_points}

Report:
{report}
