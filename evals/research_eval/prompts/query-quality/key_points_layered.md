---
id: key_points_layered
version: 2
skill: none
used_by: key points for the question (key_points.py), decomposition_coverage, material_coverage, comprehensiveness; key point method comparison (key_points_methods.py)
---

You are planning a research report. List the distinct aspects that a
thorough, well-researched answer to the question below must address,
in two layers.

- aspects: 4 to 6 main aspects. Each is a short noun phrase (at most 8
  words), specific to this question, about its subject (not about the
  report: no "scope", "methodology", "introduction" or "conclusion"). No two
  aspects overlap.
- For each aspect, 2 to 4 sub-points: the specific things a good answer says
  about it, each naming one thing (at most 10 words).
  - Name what this question is about: the actors, rules, products, markets,
    figures or events it asks for. A sub-point that would fit any question
    of its kind ("pricing", "security", "trade-offs") is too generic.
  - A sub-point is content, never an instruction for writing the report
    ("define the period", "compare the vendors", "cite sources").

Return ONLY JSON:
{"aspects": [{"aspect": "...", "sub_points": ["...", "..."]}]}

@user

Question: {question}
