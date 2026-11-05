---
id: comprehensiveness
version: 1
used_by: comprehensiveness
---

You are checking which aspects of a research question a finished report covers.
For EACH numbered key point decide:
- "full": the report gives real information on it (facts, analysis), not just a mention;
- "partial": the report touches it only briefly or vaguely;
- "none": the report does not address it.
Quote the report words your answer rests on (empty for "none").

Question:
{question}

Key points:
{key_points}

Report:
{report}

Return ONLY JSON, one entry per key point, in order:
{"points": [{"point": 1, "coverage": "full", "evidence": "..."}]}
