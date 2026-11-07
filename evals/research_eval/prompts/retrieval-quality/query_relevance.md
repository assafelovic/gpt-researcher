---
id: query_relevance
version: 8
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
- relevance_evidence: quote the words of the material that give what the
  query under review asks for, or say that it is not there.
- relevance:
  - 2: the material gives what the query under review asks for (the
    multiples, the ranking, the named bank's deployment), and that serves
    the core query, about the same subject: the same industry, the same
    kind of actor.
  - 1: the material is on the topic of the core query but does not give
    what the query asks for: background, definitions, another industry or
    kind of actor, a general study, a vendor's claims about its own
    product, or a listing page with no content.
  - 0: every passage is off the subject of the core query, such as job
    listings, page furniture or another meaning of a word.
- substance_evidence: quote the most concrete fact in the material about
  what the query asks, or say that there is none.
- substance:
  - 2: your substance_evidence quotes at least one concrete fact (as
    defined above) about what the query asks. One is enough, even among
    general text.
  - 1: the material has only general statements, forecasts, or concrete
    facts about other subjects than the query asks.
  - 0: no fact at all: marketing, definitions, page furniture or cut-off
    text.

## Judging the unit
- A query can find exactly what it asked for and still not help the core
  query: then relevance is 1.
- Judge relevance and substance apart: an on-topic explainer with no facts
  is relevance 1, substance 0.
- Decide from your evidence: relevance 2 only when your relevance_evidence
  quotes what the query asks for. If it has to say that is not there,
  relevance is 1 or 0.
- Shared words are not shared subject: an article on nursing-home handoff
  software is not about bank call centres because both mention "handoff"
  and "compliance".
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
