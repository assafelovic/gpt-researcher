---
id: domain_authority
version: 7
used_by: source_authority
---

# Task: domain authority

## Goal
- Rate how authoritative each domain is as a research source.
- You are given the core question and a list of domains. Under each domain are up to three pages the agent retrieved from it: the page title and its opening words.

## What to decide for each domain
- domain: the domain exactly as given.
- reason: who runs the site and what kind of site it is, in a few words; for off_field, also the field it covers.
- kind: one of "official", "academic", "news", "specialist", "company", "low_editorial", "off_field", "unreliable", "unknown".
- Write the reason first and pick the kind from it.

## Answer format
Return ONLY JSON, one entry per domain, in order:
{"domains": [{"domain": "example.com", "reason": "established technology news outlet", "kind": "news"}]}

@user

Core question:
{question}

Domains:
{domains}
