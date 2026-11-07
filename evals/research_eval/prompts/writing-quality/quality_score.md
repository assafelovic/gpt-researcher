---
id: quality_score
version: 4
used_by: insight, readability
---

# Task: insight and readability scores

## Goal
- You are grading a research report on an absolute scale, criterion by
  criterion.
- You are given the core query, the rubric criteria (each with an id and a
  dimension) and the report.

## What to decide for each criterion
- evidence: quote or point to the report text the score rests on.
- score: 0 to 10, by the score anchors above.

## Scoring
- Score each criterion on its own: a weak criterion does not pull the
  others down.
- Score the report as written, not what it could have said.
- A report that does what the description asks, specifically for this
  question and without gaps, is 7-8. Keep 9-10 for work a demanding expert
  would not improve.

## Insights found
- Also list the report's insights as you read them: each conclusion,
  comparison or implication that goes beyond restating a source, in one
  sentence, with the report text it comes from.
- Use an empty list if there are none.

## Answer format
Return ONLY JSON, one score entry per criterion id, in order:
{"scores": [{"id": "I1", "evidence": "...", "score": 0}], "insights": [{"insight": "...", "quote": "..."}]}

@user

Question:
{question}

Criteria:
{criteria}

Report:
{report}
