---
id: key_points_structured
version: 1
skill: none
used_by: key point method comparison (key_points_methods.py)
---

You are planning a research report. List the key points: the distinct
aspects that a thorough, well-researched answer to the question below must
address.

Work in two steps.
1. asked: list what the question itself asks for, part by part: its subject,
   the things it asks to identify, compare or describe, and the words that
   set its scope (a period such as "recent", a region, a ranking such as
   "top" or "leading").
2. key_points: the aspects a thorough answer must address. Start from the
   parts in step 1, then add the aspects a careful researcher would expect
   any good answer to cover.

Rules for key points:
- Each is a short noun phrase (at most 12 words), specific to this question.
- Each names one aspect. Join two things only when they are one aspect
  ("pricing tiers and their limits"), never three or more.
- About the subject of the question, not about the report: no "scope of the
  comparison", "methodology", "introduction" or "conclusion".
- They must not overlap: no two points that the same paragraph would answer.
- Between 4 and 8, depending on how broad the question is.

Return ONLY JSON: {"asked": ["..."], "key_points": ["...", "..."]}

@user

Question: {question}
