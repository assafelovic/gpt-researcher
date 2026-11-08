---
id: paragraph_audit
version: 10
used_by: citation audit (citation_audit.py), source_utilization, citation_recall, citation_precision, effective_citations, faithfulness
---

# Task: paragraph audit

## Goal
- You are checking one paragraph of a research report against the source material the writer had.
- You are given the core question, the paragraph as numbered items (with the sources each item cites) and the material.

## Steps (in this order)
1. kind:
   - "factual": the paragraph states facts, figures, events or findings.
   - "non_factual": only opinion, recommendation, transition or structure.
   - For a non_factual paragraph return an empty "claims" list, and still do step 3.
2. claims: split the paragraph into claims as the system prompt defines them.
   - Items without a citation count too.
   - For each claim, in this order:
     - "claim": the claim, self-contained;
     - "type": "fact" or "analysis";
     - "sentences": the item numbers it comes from;
     - "passages": the passage ids it rests on (empty when none);
     - "evidence": the material words the verdict rests on, quoted; when nothing backs the claim, say what the material gives instead;
     - "verdict": "supported", "inferred", "unsupported" or "contradicted".
3. sentences: ONLY for the items that cite sources (listed with "cites"). "sentence" is the item number, and "the sentence" means the whole item.
   - "supported": do the cited sources TOGETHER fully support everything the item states? Partial support is false.
   - For each cited source:
     - "alone": does this source by itself fully support the item?
     - "rest_suffice": with this source removed, would the item's other cited sources still fully support it? (false when it is the only citation)

## Rules
- Split by the system prompt's rules: atomic claims; a figure or a qualifier stays with its statement.
- A claim whose evidence has to say the material gives none of it is unsupported, whatever its type.
- A cited source shown as not available supports nothing.

## Output
Return ONLY JSON:
{"kind": "factual",
  "claims": [{"claim": "...", "type": "fact", "sentences": [1], "passages": ["1a"],
               "evidence": "...", "verdict": "supported"}],
  "sentences": [{"sentence": 1, "supported": true,
                  "citations": [{"source": 1, "alone": true, "rest_suffice": false}]}]}

@user

Core question of the report:
{question}

Paragraph (numbered items; "cites" lists the sources an item links to; a
citation vouches for the whole item it ends, which may be several sentences):
{sentences}

Material:
{material}
