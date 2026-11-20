---
id: claim_recheck
version: 13
used_by: citation audit recheck (citation_audit.py)
---

# Task: claim recheck

## Goal
- You are checking claims from a research report against source material.
- These claims were not fully supported by the material checked so far.
- The material below is more of what the writer had retrieved, picked by the checker for each claim: after each claim are the passages picked for it. Judge each claim against all the material shown, not only its own passages.
- The material may also hold a passage an earlier check read as contradicting a claim: judge it afresh by the rules below.

## Verdicts
- Use the four verdicts of the system prompt: supported, inferred, unsupported, contradicted.
- Several passages may be put together: a claim that only follows from two or more passages taken together is inferred, not unsupported.
- "contradicted": a passage about exactly the same thing (subject, scope, definition, period, etc.) states the opposite or a different figure. A claim that differs from the passage in any such respect is "unsupported".

## Rules
- "Exploring regional routes" does not support "competes in regional delivery".
- A statement about retail does not support the same claim about banking.
- One example does not support a general statement.
- "Is built around X" does not support "is distinguished by X".

## Output
For EACH claim, in this order: "claim" (its number), "passages" (the ids a supported, inferred or contradicted verdict rests on), "evidence" (the words quoted), "verdict".
Return ONLY JSON:
{"claims": [{"claim": 1, "passages": [], "evidence": "", "verdict": "unsupported"}]}

@user

Core question of the report:
{question}

Claims:
{claims}

Material:
{material}
