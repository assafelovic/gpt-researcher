---
id: quality_rubric
version: 2
used_by: insight, readability
---

You are preparing a grading rubric for research reports that answer the question
below. Write criteria for two dimensions, specific to THIS question:

- insight: depth of analysis, e.g. comparisons, causes and effects, trade-offs,
  synthesis across sources, a clear and justified conclusion, beyond listing facts.
- readability: logical progression of sections, explained terminology, concise
  and clear wording, appropriate use of structure (headings, lists, tables).

Give 3 to 5 criteria per dimension. Each criterion has a short name, one
sentence saying what a strong report does on it for this question, and a weight;
weights within a dimension sum to 1.

Return ONLY JSON:
{"insight": [{"criterion": "...", "description": "...", "weight": 0.3}],
  "readability": [{"criterion": "...", "description": "...", "weight": 0.3}]}

@user

Question:
{question}
