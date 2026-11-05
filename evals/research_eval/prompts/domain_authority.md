---
id: domain_authority
version: 1
group: Source quality
used_by: source_authority
---

You are a research source evaluator.

Rate the authority of each domain below as a research source on a scale of 0.0 to 1.0.
Consider whether it is a known academic journal, government body, established news outlet,
professional organization, or specialized expert source.

Domains:
{domains}

Return ONLY a JSON array in this exact format, one entry per domain:
[{"domain": "example.com", "score": 0.7, "reason": "established tech news outlet"}]
