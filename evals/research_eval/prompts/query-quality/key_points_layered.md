---
id: key_points_layered
version: 1
skill: none
used_by: key point method comparison (key_points_methods.py)
---

You are planning a research report. List the key points: the distinct
aspects that a thorough, well-researched answer to the question below must
address, in two layers.

- aspects: 4 to 6 main aspects. Each is a short noun phrase (at most 8
  words), specific to this question, about its subject (not about the
  report: no "scope", "methodology", "introduction" or "conclusion"). No two
  aspects overlap.
- For each aspect, 2 to 4 sub-points: the specific things a good answer says
  about it, each naming one thing (at most 10 words).

Return ONLY JSON:
{"aspects": [{"aspect": "...", "sub_points": ["...", "..."]}]}

@user

Question: {question}
