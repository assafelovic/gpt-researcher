---
id: topic_relevance
version: 2
used_by: topic_relevance
---

You are checking whether each paragraph of a research report serves the report's
core question. For EACH numbered paragraph answer:
- "yes": it helps answer the question (background the question needs counts);
- "no": it is off-topic or padding unrelated to the question;
- "idk": you cannot tell (e.g. a short transition).
Give a short reason for every "no".

Return ONLY JSON, one entry per paragraph, in order:
{"verdicts": [{"paragraph": 1, "verdict": "yes", "reason": ""}]}

@user

Core question:
{question}

Paragraphs:
{paragraphs}
