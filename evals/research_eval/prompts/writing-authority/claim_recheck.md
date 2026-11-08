---
id: claim_recheck
version: 12
used_by: citation audit recheck (citation_audit.py)
---

# Task: claim recheck

## Goal
- You are checking claims from a research report against source material.
- These claims were not fully supported by the material checked so far.
- The material below is more of what the writer had retrieved, picked by the checker. It may also hold a passage an earlier check read as contradicting a claim: judge it afresh by the rules below.

## Verdicts (stricter than the system prompt: there is no "inferred" here)
- "supported": one passage states the claim itself, with the same subject (entity, market, sector, region, period, etc.) and the same strength.
- "contradicted": a passage about exactly the same thing (subject, scope, definition, period, etc.) states the opposite or a different figure. A claim that differs from the passage in any such respect is "unsupported".
- "unsupported": anything else, including partial support and support that needs a step of reasoning.

## Rules
- "Exploring regional routes" does not support "competes in regional delivery".
- A statement about retail does not support the same claim about banking.
- One example does not support a general statement.
- "Is built around X" does not support "is distinguished by X".

## Output
For EACH claim, in this order: "claim" (its number), "passages" (the ids a supported or contradicted verdict rests on), "evidence" (the words quoted), "verdict".
Return ONLY JSON:
{"claims": [{"claim": 1, "passages": [], "evidence": "", "verdict": "unsupported"}]}

@user

Core question of the report:
{question}

Claims:
{claims}

Material:
{material}
