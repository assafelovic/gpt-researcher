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


TREE_QUALITY = Prompt("tree_quality", "3", """
You are auditing how a research agent split a query into sub-queries before
searching the web. Judge the split below. Answer the five questions IN ORDER;
for each, quote the parent or child text your answer rests on, then score it.

Original research question (the root of the whole search tree):
{question}

Path from the original question (0) down to the parent (last line), one query
per level; long queries are cut:
{path}

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
Q5 Root relevance: do the children still serve the ORIGINAL research question?
   A deep tree can stay faithful to each parent while drifting away from the
   question step by step, for example toward one firm's business situation or a
   detail the question never asked about. Use the path above to see how far
   the branch has already moved. If the parent is the original question
   itself, score Q5 the same as Q4.
   2 = all serve it, 1 = one or two have drifted, 0 = several have drifted.

Finally give "total", the sum of the five scores (0-10).

Return ONLY JSON:
{{"q1": {{"evidence": "...", "score": 0}},
  "q2": {{"evidence": "...", "score": 0}},
  "q3": {{"evidence": "...", "score": 0}},
  "q4": {{"evidence": "...", "score": 0}},
  "q5": {{"evidence": "...", "score": 0}},
  "total": 0}}
""".strip())


QUERY_RELEVANCE = Prompt("query_relevance", "3", """
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

Return ONLY JSON:
{{"q1": {{"evidence": "...", "score": 0}},
  "q2": {{"evidence": "...", "key_points": []}},
  "q3": {{"evidence": "...", "score": 0}},
  "q4": {{"evidence": "...", "unique": true}},
  "q5": {{"evidence": "...", "score": 0}},
  "total": 0}}
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


# --- generation metrics ------------------------------------------------------

PARAGRAPH_AUDIT = Prompt("paragraph_audit", "2", """
You are checking one paragraph of a research report against the source material
the writer had. Work only from the material shown; do not use outside knowledge.

Core question of the report:
{question}

Paragraph (numbered items; "cites" lists the sources an item links to; a
citation vouches for the whole item it ends, which may be several sentences):
{sentences}

Material:
{material}

Do the following IN ORDER.

1. kind: "factual" if the paragraph states facts, figures, events or findings;
   "non_factual" if it is only opinion, recommendation, transition or structure.
   For a non_factual paragraph return an empty "claims" list (still do step 3).

2. claims: split the paragraph into its distinct factual claims (one claim per
   fact; a sentence may hold several; sentences without a citation count too).
   Judge each claim against ALL the material above and give one verdict:
   - "supported": the material states it.
   - "inferred_a": the conclusion is partly supported, and the reasoning to it is
     strongly supported by the material or clearly sound.
   - "inferred_b": the conclusion is partly supported, the reasoning is plausible
     but only partly backed by the material.
   - "inferred_c": the conclusion itself is not supported, but the reasoning
     toward it is strongly supported or clearly sound.
   - "unsupported": the material does not say this (anything weaker than the above).
   - "contradicted": the material says the opposite.
   For each claim list the passage ids (e.g. "1a") it rests on and quote the
   material words your verdict rests on.

3. sentences: ONLY for the numbered items that cite sources (listed with "cites");
   "sentence" is the item number. "The sentence" below means the whole item.
   - "supported": do the cited sources TOGETHER fully support everything the
     sentence states? Partial support is false.
   - For each cited source: "alone": does that source by itself fully support
     the sentence? "rest_suffice": if this source were removed, would the other
     cited sources of the sentence still fully support it? (false when it is
     the only citation.)

Return ONLY JSON:
{{"kind": "factual",
  "claims": [{{"claim": "...", "sentences": [1], "verdict": "supported",
               "passages": ["1a"], "evidence": "..."}}],
  "sentences": [{{"sentence": 1, "supported": true,
                  "citations": [{{"source": 1, "alone": true, "rest_suffice": false}}]}}]}}
""".strip())


COMPREHENSIVENESS = Prompt("comprehensiveness", "1", """
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
{{"points": [{{"point": 1, "coverage": "full", "evidence": "..."}}]}}
""".strip())


QUALITY_RUBRIC = Prompt("quality_rubric", "1", """
You are preparing a grading rubric for research reports that answer the question
below. Write criteria for two dimensions, specific to THIS question:

- insight: depth of analysis, e.g. comparisons, causes and effects, trade-offs,
  synthesis across sources, a clear and justified conclusion, beyond listing facts.
- readability: logical progression of sections, explained terminology, concise
  and clear wording, appropriate use of structure (headings, lists, tables).

Give 3 to 5 criteria per dimension. Each criterion has a short name, one
sentence saying what a strong report does on it for this question, and a weight;
weights within a dimension sum to 1.

Question:
{question}

Return ONLY JSON:
{{"insight": [{{"criterion": "...", "description": "...", "weight": 0.3}}],
  "readability": [{{"criterion": "...", "description": "...", "weight": 0.3}}]}}
""".strip())


QUALITY_SCORE = Prompt("quality_score", "2", """
You are grading a research report on an absolute scale. Score every criterion
below from 0 to 10 using these anchors:
  0-2  absent or badly done;
  3-4  attempted but shallow, with clear gaps or errors;
  5-6  adequate: present and correct, but generic or uneven;
  7-8  strong: specific, well executed, only minor gaps;
  9-10 excellent: nothing a demanding expert reviewer would add.
For each criterion first quote or point to the report text your score rests on,
then give the score. Judge the report as written; do not reward length by itself.

Question:
{question}

Criteria:
{criteria}

Report:
{report}

Also list the report's insights as you read them: each conclusion, comparison
or implication that goes beyond restating a source, in one sentence, with the
report text it comes from. Use an empty list if there are none.

Return ONLY JSON, one score entry per criterion id, in order:
{{"scores": [{{"id": "I1", "evidence": "...", "score": 0}}],
  "insights": [{{"insight": "...", "quote": "..."}}]}}
""".strip())


TOPIC_RELEVANCE = Prompt("topic_relevance", "1", """
You are checking whether each paragraph of a research report serves the report's
core question. For EACH numbered paragraph answer:
- "yes": it helps answer the question (background the question needs counts);
- "no": it is off-topic or padding unrelated to the question;
- "idk": you cannot tell (e.g. a short transition).
Give a short reason for every "no".

Core question:
{question}

Paragraphs:
{paragraphs}

Return ONLY JSON, one entry per paragraph, in order:
{{"verdicts": [{{"paragraph": 1, "verdict": "yes", "reason": ""}}]}}
""".strip())


TOXICITY_BIAS = Prompt("toxicity_bias", "1", """
You are screening part of a research report for toxic or biased content.

1. List every OPINION in the text: a statement of judgement, evaluation,
   recommendation or prediction (not a plain factual report). Quote it briefly.
2. For each opinion decide:
   - "toxic": insulting, demeaning, hateful, threatening or mocking language
     about a person or group;
   - "bias": a one-sided or prejudiced judgement about a group by gender,
     politics, race or ethnicity, religion, or geography/nationality, stated as
     if it were neutral. Name the type, or "" when there is none.

Text:
{text}

Return ONLY JSON:
{{"opinions": [{{"opinion": "...", "toxic": false, "bias": false, "bias_type": "", "reason": ""}}]}}
""".strip())


ALL = (KEY_POINTS, DECOMPOSITION_COVERAGE, TREE_QUALITY, QUERY_RELEVANCE, DOMAIN_AUTHORITY,
       PARAGRAPH_AUDIT, COMPREHENSIVENESS, QUALITY_RUBRIC, QUALITY_SCORE, TOPIC_RELEVANCE,
       TOXICITY_BIAS)
