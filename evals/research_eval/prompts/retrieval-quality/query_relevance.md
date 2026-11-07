---
id: query_relevance
version: 6
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
  - 2: the material gives information the core query asks for.
  - 1: the material is on the topic but does not give that information:
    background, definitions, related subjects, or a vendor's claims about
    its own product.
  - 0: every passage is off the subject of the core query.
- substance_evidence: quote the most concrete fact in the material about
  what the query asks, or say that there is none.
- substance:
  - 2: your substance_evidence quotes at least one concrete fact about what
    the query asks: a figure, a date, or a named deal, organisation, rule
    or product. One such fact is enough, even among general text.
  - 1: the material has facts, but only general statements or facts about
    other subjects than the query asks.
  - 0: no fact at all: marketing, definitions, page furniture or cut-off
    text.

## Judging the unit
- Relevance is to the core query, not to the query under review: a query
  can find exactly what it asked for and still not help the core query.
- Judge relevance and substance apart: an on-topic explainer with no facts
  is relevance 1, substance 0.
- Decide from your evidence: if your relevance_evidence has to say the
  material does not give what is asked, relevance is not 2.
- Keep relevance 0 for material wholly off the subject (another industry,
  another meaning of a word): it sets the unit's score to 0.
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
