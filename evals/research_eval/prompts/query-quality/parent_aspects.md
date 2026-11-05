---
id: parent_aspects
version: 3
used_by: decomposition_tree_quality
---

You are planning research on one query from a research agent's search tree.
List the distinct aspects of the query below that a good answer to it must
cover. Judge the query alone: you are not shown how the agent split it.

@include query-quality#principles

What counts as an aspect:
@include query-quality#aspect

Return ONLY JSON, between 2 and 6 aspects, each a short phrase:
{"aspects": ["...", "..."]}

@user

Original research question (the root of the whole search tree), for context
only; list the aspects of the query, not of the question:
{question}

Query:
{parent}
