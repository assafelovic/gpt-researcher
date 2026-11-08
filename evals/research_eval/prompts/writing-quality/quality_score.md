---
id: quality_score
version: 7
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
- gaps: what a demanding expert would still want on this criterion for
  this question, as a short list; empty when there is nothing.
- score: 0 to 10, from the gaps:
  - 9-10: no gaps.
  - 7-8: one or two minor gaps.
  - 5-6: a clear gap, or several minor ones; the criterion is met only in
    general terms.
  - 3-4: the criterion is attempted but mostly unmet.
  - 0-2: absent or badly done.

## Scoring
- Score each criterion on its own: a weak criterion does not pull the
  others down.
- Score the report as written, not what it could have said.
- Write the gaps before the score, and let the score follow from them.

## Insights found
- Also list the report's insights as you read them: each conclusion,
  comparison, implication, etc. that goes beyond restating a source, in one
  sentence, with the report text it comes from.
- Use an empty list if there are none.

## Answer format
Return ONLY JSON, one score entry per criterion id, in order:
{"scores": [{"id": "I1", "evidence": "...", "gaps": ["..."], "score": 0}], "insights": [{"insight": "...", "quote": "..."}]}

@user

Question:
{question}

Criteria:
{criteria}

Report:
{report}
