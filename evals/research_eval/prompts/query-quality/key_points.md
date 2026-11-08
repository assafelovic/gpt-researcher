---
id: key_points
version: 2
skill: none
used_by: key point method comparison (key_points_methods.py, "current"); the key points until key_points_layered replaced it
---

You are planning a research report. List the distinct aspects that a thorough,
well-researched answer to the question below must address.

Rules:
- Between 3 and 8 aspects, depending on how broad the question is.
- Each aspect is a short noun phrase (at most 12 words), specific to this question.
- Aspects must not overlap; do not include generic items like "introduction" or "conclusion".

Return ONLY JSON: {"key_points": ["...", "..."]}

@user

Question: {question}
