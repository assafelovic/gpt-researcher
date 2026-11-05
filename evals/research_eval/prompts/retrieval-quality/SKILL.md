---
name: retrieval-quality
description: How the judge rates what a research agent retrieved before writing (whether the material covers the question's key points, whether each sub-query brought back relevant material). Shared by the prompts of material_coverage and query_relevance.
---

# Retrieval quality

This group judges the material the agent kept, before any report is written.
Prompts in this folder include shared sections with
`@include retrieval-quality#<section>`; the text under a `## <section>`
heading is sent to the judge as it is.

No shared sections yet: they are written when this group is reviewed in
stage 2, so its prompts are judged again only once. Candidates: the
full / partial / none coverage scale (material_coverage.md, also used by
writing-quality/comprehensiveness.md) and what counts as relevant material.
