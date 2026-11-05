---
id: tree_quality
version: 4
used_by: decomposition_tree_quality
---

You are auditing how a research agent split a query into sub-queries before
searching the web. Judge each child query on its own, then the split as a
whole. For every answer, quote the parent or child words it rests on.

Original research question (the root of the whole search tree):
{question}

Path from the original question (0) down to the parent (last line), one query
per level; long queries are cut:
{path}

Parent query:
{parent}

Child queries:
{children}

For EACH child, answer true or false:
- narrower: it asks for one part of the parent, or a more concrete angle on
  it. False when it restates the whole parent in other words.
- searchable: pasted into a web search engine as it is, it would return
  focused results. False when it is too vague, or a pile of terms about
  several different things.
- serves_parent: what it asks helps answer the parent. Moderate extension
  beyond the parent's literal scope counts when it helps answer it.
- serves_question: it still serves the ORIGINAL research question. A deep
  tree can stay faithful to each parent while drifting away from the question
  step by step, for example toward one firm's business situation or a detail
  the question never asked about. Use the path above to see how far the
  branch has already moved. If the parent is the original question itself,
  give the same answer as serves_parent.

Then, for the split as a whole, list the distinct aspects of the parent (at
most 6, each a short phrase) and, for each aspect, the numbers of the children
aimed at it (an empty list when no child picks it up).

Return ONLY JSON:
{"children": [{"child": 1, "narrower": true, "searchable": true,
                "serves_parent": true, "serves_question": true, "evidence": "..."}],
  "aspects": [{"aspect": "...", "children": [1]}]}
