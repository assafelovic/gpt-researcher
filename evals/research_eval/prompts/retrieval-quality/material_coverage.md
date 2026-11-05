---
id: material_coverage
version: 1
used_by: material_coverage
---

You are checking which aspects of a research question the material a research
agent retrieved covers, before any report is written. Under each numbered key
point are the retrieved passages that match it best (a sample, picked by word
overlap). For EACH key point decide, from the passages shown (under any key
point):
- "full": they give real information on it (facts, figures, explanations),
  enough to write a paragraph about it;
- "partial": they touch it only briefly or vaguely;
- "none": no passage addresses it.
Name the passage ids your answer rests on and quote their words (empty for "none").

Question:
{question}

{points}

Return ONLY JSON, one entry per key point, in order:
{"points": [{"point": 1, "coverage": "full", "passages": ["1a"], "evidence": "..."}]}
