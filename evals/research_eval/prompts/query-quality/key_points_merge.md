---
id: key_points_merge
version: 1
skill: none
used_by: key point method comparison (key_points_methods.py)
---

Several lists of key points were written for the same research question.
Group the points that name the same aspect of the question, so each group
is one aspect.

Rules:
- Put two points in one group only when the same paragraph of a report
  would answer both. Shared words are not enough.
- A point that names two aspects goes in the group of the aspect it is
  mainly about.
- Every point goes in exactly one group; a group may hold one point.
- name: a short noun phrase for the aspect.
- about_report: true when the aspect is about the report itself (its scope,
  method or structure) rather than the subject of the question.

Return ONLY JSON:
{"groups": [{"name": "...", "points": ["L1.2", "L3.1"], "about_report": false}]}

@user

Question: {question}

Lists (each point has an id: list number . point number):
{lists}
