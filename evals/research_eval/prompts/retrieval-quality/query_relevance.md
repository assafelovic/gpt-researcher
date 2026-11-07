---
id: query_relevance
version: 12
used_by: query_relevance
---

# Task: query relevance

## Goal
- You are auditing one retrieval step of a research agent: one query it
  searched and the material it kept for it.
- Judge the query and its material together, as one unit, against the core
  query.
- You are given the core query, the query under review and the material,
  one passage per page, best matches first.

## What to decide
- relevance_evidence: quote the words of the material that decide its
  relevance.
- relevance:
  - 2: the material gives information the core query asks for, about the
    same subject: the same industry, the same kind of actor.
  - 1: the material is near the topic but does not give that information:
    background, definitions, another industry or kind of actor, a general
    study, or a vendor's claims about its own product.
  - 0: every passage is off the subject of the core query or has nothing
    to judge: job listings, page furniture, a repository or file listing,
    a video page with no transcript, a list of links, or another meaning
    of a word.
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
- Relevance is to the core query, not to the query under review: a query
  can find exactly what it asked for and still not help the core query.
- Judge relevance and substance apart: an on-topic explainer with no facts
  is relevance 1, substance 0.
- Decide from your evidence: if your relevance_evidence has to say the
  material does not give what is asked, relevance is not 2.
- The query names a year and the material's facts are two or more years
  older: relevance is at most 1.
- Shared words are not shared subject: an article on nursing-home handoff
  software is not about bank call centres because both mention "handoff"
  and "compliance".
- Keep relevance 0 for material wholly off the subject (another industry,
  another meaning of a word): it sets the unit's score to 0.
- Other queries of the same plan are not shown: whether two queries repeat
  each other is judged elsewhere.

## Answer format
Return ONLY JSON:
{"relevance_evidence": "...", "relevance": 2, "substance_evidence": "...", "substance": 1}

@user

Core question:
{question}

Query under review:
{query}

Material retrieved for it:
{material}
