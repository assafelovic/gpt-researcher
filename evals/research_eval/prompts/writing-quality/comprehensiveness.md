---
id: comprehensiveness
version: 7
used_by: comprehensiveness
---

# Task: comprehensiveness

## Goal
- You are checking which aspects of the question a finished report covers.
- You are given the core query, its numbered key points and the report.
- Under a key point, "includes" lists the sub-points a good answer gives on
  it. They show what the point means; the point is still judged as a whole.

## What to decide for each key point
- evidence: quote the report words your answer rests on. Empty for "none".
- coverage: "full", "partial" or "none", by the definitions above.

## Covered or not
- Look through the whole report before deciding, and judge each point by
  the report's strongest passage on it, not the first one you find.
- Sharing the point's words is not enough: the report must say something
  about the point itself.
- Naming an example that belongs to the point (a company, a place, a
  product, etc.) does not cover it unless the report says something about the
  point.
- A point is full when the report gives real information on the point and
  on most of what it includes; when it covers only some of it, it is
  partial. The same holds for a point that names several parts ("costs,
  timelines and risks").
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
