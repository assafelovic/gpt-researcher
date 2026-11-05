---
name: writing-authority
description: How the judge checks the report against the material the writer had (splitting paragraphs into claims, fact or analysis, supported or not, whether each citation backs its sentence). Shared by the prompts of the citation audit, which feeds source_utilization, citation_recall, citation_precision, effective_citations and faithfulness.
---

# Writing authority

This group judges whether the report says only what its sources support.
Prompts in this folder include shared sections with
`@include writing-authority#<section>`; the text under a `## <section>`
heading is sent to the judge as it is.

No shared sections yet: they are written when this group is reviewed in
stage 2, so its prompts are judged again only once. Candidates: what a claim
is, fact versus analysis, and the verdict scale (supported, inferred,
unsupported, contradicted), now stated in paragraph_audit.md and, more
strictly, in claim_recheck.md.
