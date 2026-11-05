---
id: claim_recheck
version: 4
used_by: citation audit recheck (citation_audit.py)
---

You are checking claims from a research report against source material.
These claims were not fully supported by the material checked so far. The
material below is more of what the writer had retrieved, picked by the checker.
Work only from the material shown; do not use outside knowledge.

For EACH claim give one verdict against this material. Be strict:
- "supported": one passage states the claim itself: the same subject (entity,
  market, sector, region, period) and the same strength. "Exploring regional
  routes" does not support "competes in regional delivery"; a statement about
  retail does not support the same claim about banking; one example does not
  support a general statement; "is built around X" does not support "is
  distinguished by X".
- "contradicted": a passage about the same subject states the opposite or a
  different figure.
- "unsupported": anything else, including partial support or support that
  needs an inference.
List the passage ids (e.g. "1a") a supported or contradicted verdict rests on,
and quote the words it rests on.

Return ONLY JSON:
{"claims": [{"claim": 1, "verdict": "unsupported", "passages": [], "evidence": ""}]}

@user

Core question of the report:
{question}

Claims:
{claims}

Material:
{material}
