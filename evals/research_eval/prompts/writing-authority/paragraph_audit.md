---
id: paragraph_audit
version: 5
used_by: citation audit (citation_audit.py), source_utilization, citation_recall, citation_precision, effective_citations, faithfulness
---

You are checking one paragraph of a research report against the source material
the writer had. Work only from the material shown; do not use outside knowledge.

Do the following IN ORDER.

1. kind: "factual" if the paragraph states facts, figures, events or findings;
   "non_factual" if it is only opinion, recommendation, transition or structure.
   For a non_factual paragraph return an empty "claims" list (still do step 3).

2. claims: split the paragraph into claims. A claim is
   - checkable: someone holding the right source could say whether it is true;
   - atomic: one piece of information (split "A and B" when each can be checked
     on its own; keep a figure together with what it measures);
   - self-contained: understandable without the paragraph (replace pronouns;
     never refer to item or source numbers such as "item 1" or "[2]").
   Sentences without a citation count too. Give each claim a type:
   - "fact": an event, number, date, an entity's action or property, or what a
     named source found or said. A source could state it word for word.
     "Gartner ranks Zipline first" is a fact: that Gartner says so is checkable.
     What a named entity is or does (its role, type, specialty, business model,
     products, partners, markets) is a fact, even when worded loosely: a source
     can confirm or deny it. If unsure, use fact.
   - "analysis": the writer's own evaluation, ranking, comparison, prediction,
     recommendation or conclusion, or a statement about the report or its
     sources. No source would state it as such; at best it follows from them.
   Examples:
     "Swoop Aero is a healthcare logistics specialist."                -> fact
     "Wing's role is as a delivery operator for retail partners."      -> fact
     "Zipline's model is per-delivery fees paid by health systems."    -> fact
     "Zipline has completed over one million deliveries."              -> fact
     "Zipline has completed over one million deliveries, the most of
      any operator."  -> two claims, both fact if the material ranks them
     "Zipline has the strongest claim to leadership in drone delivery." -> analysis
     "Banks should start with low-risk chatbot use cases."              -> analysis
     "Both sources agree on the timeline."                              -> analysis
     "Revenue doubled from 2023 to 2024." (from two figures)             -> fact
   A sentence holding both kinds is split into a fact and an analysis claim.
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
   For each claim list the item numbers it comes from, the passage ids (e.g.
   "1a") it rests on, and quote the material words your verdict rests on.

3. sentences: ONLY for the numbered items that cite sources (listed with "cites");
   "sentence" is the item number. "The sentence" below means the whole item.
   - "supported": do the cited sources TOGETHER fully support everything the
     sentence states? Partial support is false.
   - For each cited source: "alone": does that source by itself fully support
     the sentence? "rest_suffice": if this source were removed, would the other
     cited sources of the sentence still fully support it? (false when it is
     the only citation.)

Return ONLY JSON:
{"kind": "factual",
  "claims": [{"claim": "...", "type": "fact", "sentences": [1], "verdict": "supported",
               "passages": ["1a"], "evidence": "..."}],
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
