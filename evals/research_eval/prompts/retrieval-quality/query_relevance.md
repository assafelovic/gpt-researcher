---
id: query_relevance
version: 4
used_by: query_relevance
---

You are auditing one retrieval step of a research agent. The agent searched the
web with a sub-query and kept the material shown below. Judge the sub-query and
its material TOGETHER as one unit, against the core research question. Answer
the five questions IN ORDER. For every answer quote the sub-query or material
text it rests on.

Q1 Topic relevance: does the unit serve the core question? 0 = no, 1 = partly, 2 = yes.
Q2 Key points: which of the numbered key points does the material give real
   information about? List their numbers (may be empty).
Q3 Specificity: is the material concrete (facts, figures, named entities,
   dates) rather than generic? 0 / 1 / 2.
Q4 Uniqueness: compared with the other sub-queries listed (the ones at the same
   level of the research plan), does this one go after something they do not?
   Answer false ONLY when another listed sub-query asks for the same
   information in other words, so that both would be answered by the same
   facts. A different perspective, a different source or authority, or a
   separate subtopic about the same object counts as unique, even when the
   wording overlaps heavily. true / false.
Q5 Usability: could a writer cite this material directly in the report? 0 / 1 / 2.

Then give "total" from 0 to 10: your overall judgement of how much this unit
contributes to answering the core question.

Examples (abbreviated):
- Good (total 9): core "EV battery supply chain risks"; sub-query "cobalt supply
  concentration DRC 2024"; material gives DRC's share of cobalt output and named
  refiners. Q1=2, Q2=[2], Q3=2, Q4=true, Q5=2.
- Medium (total 5): same core; sub-query "electric vehicles overview"; material
  is a general explainer with one paragraph on batteries. Q1=1, Q2=[], Q3=1,
  Q4=false, Q5=1.
- Poor (total 1): same core; sub-query "best EV models to buy"; material is car
  reviews. Q1=0, Q2=[], Q3=1, Q4=true, Q5=0.

Return ONLY JSON:
{"q1": {"evidence": "...", "score": 0},
  "q2": {"evidence": "...", "key_points": []},
  "q3": {"evidence": "...", "score": 0},
  "q4": {"evidence": "...", "unique": true},
  "q5": {"evidence": "...", "score": 0},
  "total": 0}

@user

Core question:
{question}

Key points:
{key_points}

Other sub-queries at the same level of the plan:
{other_queries}

Sub-query under review:
{query}

Material retrieved for it:
{material}
