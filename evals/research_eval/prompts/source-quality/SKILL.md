---
name: source-quality
description: How the judge rates the sources a research agent retrieved (how authoritative each domain is). Used by the prompt of source_authority; source_diversity and source_recency are computed by rules and send no prompt.
---

# Source quality

This group judges where the material came from, not what it says. Prompts in
this folder include shared sections with `@include source-quality#<section>`;
the text under a `## <section>` heading is sent to the judge as it is.

No shared sections yet: they are written when this group is reviewed in
stage 2, so its prompts are judged again only once. Candidate: what makes a
source authoritative for a research question (academic, government,
established news, professional or expert), which domain_authority.md states
inline.
