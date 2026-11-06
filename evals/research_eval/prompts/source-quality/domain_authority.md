---
id: domain_authority
version: 4
used_by: source_authority
---

# Task: domain authority

## Goal
- Rate how authoritative each domain is as a research source.
- You are given a list of domains, one per line.

## What to decide for each domain
- domain: the domain exactly as given.
- reason: who runs the site and what kind of site it is, in a few words.
- kind: one of "official", "academic", "news", "specialist", "company",
  "marketing", "low_editorial", "unreliable", "unknown".
- Write the reason first and pick the kind from it: a reason that cannot
  name the company is not "company".

## Answer format
Return ONLY JSON, one entry per domain, in order:
{"domains": [{"domain": "example.com", "reason": "established technology news outlet", "kind": "news"}]}

@user

Domains:
{domains}
