---
id: key_points
version: 1
group: Query quality
used_by: key points for the question (key_points.py), decomposition_coverage, material_coverage, query_relevance, comprehensiveness
---

You are planning a research report. List the distinct aspects that a thorough,
well-researched answer to the question below must address.

Rules:
- Between 3 and 8 aspects, depending on how broad the question is.
- Each aspect is a short noun phrase (at most 12 words), specific to this question.
- Aspects must not overlap; do not include generic items like "introduction" or "conclusion".

Question: {question}

Return ONLY JSON: {"key_points": ["...", "..."]}
