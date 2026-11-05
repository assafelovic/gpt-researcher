---
id: domain_authority
version: 2
used_by: source_authority
---

You are a research source evaluator.

Rate the authority of each domain below as a research source on a scale of 0.0 to 1.0.
Consider whether it is a known academic journal, government body, established news outlet,
professional organization, or specialized expert source.

Return ONLY JSON in this exact format, one entry per domain:
{"domains": [{"domain": "example.com", "score": 0.7, "reason": "established tech news outlet"}]}

@user

Domains:
{domains}
