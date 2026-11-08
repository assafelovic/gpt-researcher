---
id: key_points_layered
version: 4
skill: none
used_by: key points for the question (key_points.py), decomposition_coverage, material_coverage, comprehensiveness; key point method comparison (key_points_methods.py)
---

You are planning a research report. List the distinct aspects that a
thorough, well-researched answer to the question below must address,
in two layers.

- aspects: 4 to 6 main aspects. Each is a short noun phrase (at most 8
  words), specific to this question, about its subject (not about the
  report: no "scope", "methodology", "introduction", "conclusion", etc.). No two
  aspects overlap.
- For each aspect, 2 to 4 sub-points: the parts of it that a good answer
  covers, each naming one thing (at most 10 words).
  - Sub-points say what the answer must report on, not which facts it will
    find: no particular figure, date, deal, event, etc. a report may or may not
    pick. When the question asks for actors (vendors, platforms, rules, etc.), a
    sub-point may name the main ones.
  - A sub-point is content, never an instruction for writing the report
    ("define the period", "compare the vendors", "cite sources", etc.).
- Together the aspects cover the whole question: every region, kind of
  actor, part, etc. it asks about or implies.

Return ONLY JSON:
{"aspects": [{"aspect": "...", "sub_points": ["...", "..."]}]}

@user

Question: {question}
