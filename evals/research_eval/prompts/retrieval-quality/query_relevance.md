---
id: query_relevance
version: 5
used_by: query_relevance
---

# Task: query relevance

## Goal
- You are auditing one retrieval step of a research agent: one query it
  searched and the material it kept for it.
- Judge the query and its material together, as one unit, against the core
  query.
- You are given the core query, its key points, the query under review and
  the material, one passage per page, best matches first.

## What to decide
- key_points: the numbers of the key points the material gives real
  information on. May be empty.
- relevance_evidence: quote the words of the material that decide its
  relevance.
- relevance:
  - 2: most passages are about what the core query asks.
  - 1: some passages are; the rest are off topic or only background.
  - 0: no passage helps answer the core query.
- substance_evidence: quote the most concrete fact in the material, or say
  that there is none.
- substance:
  - 2: the passages give concrete facts a writer could cite: figures,
    dates, named actors, rules, decisions or results.
  - 1: a few such facts among general text.
  - 0: general text, marketing, page furniture or cut-off text only.

## Judging the unit
- Relevance is to the core query, not to the query under review: a query
  can find exactly what it asked for and still not help the core query.
- Judge relevance and substance apart: an on-topic explainer with no facts
  is relevance 2, substance 0.
- Other queries of the same plan are not shown: whether two queries repeat
  each other is judged elsewhere.

## Answer format
Return ONLY JSON:
{"key_points": [2], "relevance_evidence": "...", "relevance": 2, "substance_evidence": "...", "substance": 1}

@user

Core question:
{question}

Key points:
{key_points}

Query under review:
{query}

Material retrieved for it:
{material}
