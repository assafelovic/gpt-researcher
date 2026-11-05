---
id: quality_score
version: 2
used_by: insight, readability
---

You are grading a research report on an absolute scale. Score every criterion
below from 0 to 10 using these anchors:
  0-2  absent or badly done;
  3-4  attempted but shallow, with clear gaps or errors;
  5-6  adequate: present and correct, but generic or uneven;
  7-8  strong: specific, well executed, only minor gaps;
  9-10 excellent: nothing a demanding expert reviewer would add.
For each criterion first quote or point to the report text your score rests on,
then give the score. Judge the report as written; do not reward length by itself.

Question:
{question}

Criteria:
{criteria}

Report:
{report}

Also list the report's insights as you read them: each conclusion, comparison
or implication that goes beyond restating a source, in one sentence, with the
report text it comes from. Use an empty list if there are none.

Return ONLY JSON, one score entry per criterion id, in order:
{"scores": [{"id": "I1", "evidence": "...", "score": 0}],
  "insights": [{"insight": "...", "quote": "..."}]}
