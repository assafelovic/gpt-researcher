"""
Versioned judge prompts.
------------------------
Every prompt has an id and a version. Change the text -> bump the version: the
version is part of every cache key and is recorded with each score, so old
verdicts are never mixed with new ones. `prompt_hash` adds a content check in
case a version bump is forgotten.

All rubric prompts follow the same shape: answer a fixed list of small
questions in order, quote the text each answer rests on, then give a total.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Prompt:
    id: str
    version: str
    template: str

    @property
    def hash(self) -> str:
        return hashlib.sha256(self.template.encode("utf-8")).hexdigest()[:12]

    def render(self, **kw) -> str:
        return self.template.format(**kw)


KEY_POINTS = Prompt("key_points", "1", """
You are planning a research report. List the distinct aspects that a thorough,
well-researched answer to the question below must address.

Rules:
- Between 3 and 8 aspects, depending on how broad the question is.
- Each aspect is a short noun phrase (at most 12 words), specific to this question.
- Aspects must not overlap; do not include generic items like "introduction" or "conclusion".

Question: {question}

Return ONLY JSON: {{"key_points": ["...", "..."]}}
""".strip())


DECOMPOSITION_COVERAGE = Prompt("decomposition_coverage", "1", """
You are auditing which aspects of a research question a research agent decided
to search for. Below are the question's key points and the sub-queries the
agent searched. For EACH key point, list the numbers of the sub-queries that
are aimed at it: the sub-query names that aspect, or is clearly written to
find information about it. A sub-query that only shares broad topic words
(e.g. "crypto regulation in Europe") does not count. A sub-query may serve
several key points. Quote the words of the sub-query your answer rests on;
leave the list empty when no sub-query targets the point.

Question:
{question}

Key points:
{key_points}

Sub-queries:
{subqueries}

Return ONLY JSON, one entry per key point, in order:
{{"points": [{{"point": 1, "evidence": "...", "subqueries": [2]}}]}}
""".strip())


TREE_QUALITY = Prompt("tree_quality", "1", """
You are auditing how a research agent split a query into sub-queries before
searching the web. Judge the split below. Answer the four questions IN ORDER;
for each, quote the parent or child text your answer rests on, then score it.

Parent query:
{parent}

Child queries:
{children}

Q1 Coverage: are all aspects of the parent picked up by at least one child?
   2 = every aspect, 1 = most aspects, 0 = major aspects missing.
Q2 Specificity: are the children narrower and more concrete than the parent?
   2 = all of them, 1 = some, 0 = they mostly restate the parent.
Q3 Searchability: could each child be pasted into a web search engine as-is and
   return focused results? 2 = all, 1 = some, 0 = few or none.
Q4 Relevance: does every child serve the parent? Moderate extension beyond the
   parent's literal scope is acceptable when it helps answer it.
   2 = all relevant, 1 = one or two drift, 0 = several are off-topic.

Finally give "total", the sum of the four scores (0-8).

Return ONLY JSON:
{{"q1": {{"evidence": "...", "score": 0}},
  "q2": {{"evidence": "...", "score": 0}},
  "q3": {{"evidence": "...", "score": 0}},
  "q4": {{"evidence": "...", "score": 0}},
  "total": 0}}
""".strip())


QUERY_RELEVANCE = Prompt("query_relevance", "1", """
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
Q4 Uniqueness: compared with the other sub-queries listed, does this one go
   after something they do not? true / false.
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

Core question:
{question}

Key points:
{key_points}

Other sub-queries in this run:
{other_queries}

Sub-query under review:
{query}

Material retrieved for it:
{material}

Return ONLY JSON:
{{"q1": {{"evidence": "...", "score": 0}},
  "q2": {{"evidence": "...", "key_points": []}},
  "q3": {{"evidence": "...", "score": 0}},
  "q4": {{"evidence": "...", "unique": true}},
  "q5": {{"evidence": "...", "score": 0}},
  "total": 0}}
""".strip())


CHUNK_USED = Prompt("chunk_used", "1", """
Decide whether a research report used information from a source passage.
"Used" means at least one specific fact, figure, claim or example in the report
sentences comes from the passage. Shared topic words alone do not count.

Source passage:
{chunk}

Report sentences most similar to it:
{sentences}

Return ONLY JSON: {{"evidence": "<the sentence and passage text that match, or why none do>", "used": true}}
""".strip())


DOMAIN_AUTHORITY = Prompt("domain_authority", "1", """
You are a research source evaluator.

Rate the authority of each domain below as a research source on a scale of 0.0 to 1.0.
Consider whether it is a known academic journal, government body, established news outlet,
professional organization, or specialized expert source.

Domains:
{domains}

Return ONLY a JSON array in this exact format, one entry per domain:
[{{"domain": "example.com", "score": 0.7, "reason": "established tech news outlet"}}]
""".strip())


ALL = (KEY_POINTS, DECOMPOSITION_COVERAGE, TREE_QUALITY, QUERY_RELEVANCE, CHUNK_USED, DOMAIN_AUTHORITY)
