---
id: quality_rubric
version: 4
used_by: insight, readability
---

# Task: grading rubric

## Goal
- You are preparing a grading rubric for research reports that answer the
  question below.
- Write criteria for two dimensions, insight and readability (as defined
  above), specific to THIS question.

## What to write
- 3 to 5 criteria per dimension.
- Each criterion has:
  - criterion: a short name;
  - description: one sentence saying what a strong report does on it for
    this question;
  - weight: its share of the dimension; weights within a dimension sum
    to 1.

## Good criteria
- Each can be judged from the report text alone.
- Each names something this question needs: for insight, the comparisons,
  causes, trade-offs or conclusions a good answer to it draws; for
  readability, how clearly its content can be presented: order, structure,
  fluent and precise wording, for the reader defined above.
- A readability criterion is about the description only: never about what
  the report covers (scope, dates, which items it includes), and never asks
  to explain terms that reader already knows.
- Criteria do not overlap, and none is about length, citations or whether
  the facts are true: those are judged elsewhere.

## Answer format
Return ONLY JSON:
{"insight": [{"criterion": "...", "description": "...", "weight": 0.3}], "readability": [{"criterion": "...", "description": "...", "weight": 0.3}]}

@user

Question:
{question}
