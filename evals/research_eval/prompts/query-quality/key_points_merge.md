---
id: key_points_merge
version: 2
skill: none
used_by: key point method comparison (key_points_methods.py)
---

Several lists of key points were written for the same research question.
Find the single things they name, and group the points by them.

Rules:
- A group is one single thing a report could cover in one paragraph (the
  pricing tiers of the platforms; recycling plant capacity), not a broad
  area that holds several of them.
- Put a point in every group it names: "pricing, free tiers and usage
  costs" goes in three groups when those are three things. Most points go
  in one group.
- Two points share a group only when the same paragraph would answer both.
  Shared words are not enough.
- Every point goes in at least one group; a group may hold one point.
- name: a short noun phrase for the thing.
- about_report: true when the thing is about the report itself (its scope,
  method or structure) rather than the subject of the question.

Return ONLY JSON:
{"groups": [{"name": "...", "points": ["L1.2", "L3.1"], "about_report": false}]}

@user

Question: {question}

Lists (each point has an id: list number . point number):
{lists}
