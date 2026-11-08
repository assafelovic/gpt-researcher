---
id: key_points_synthesize
version: 2
skill: none
used_by: key points for the question when drafts > 1 (key_points.py); key point method comparison (key_points_methods.py, "layered-merged")
---

Below are several drafts of the key points of a research question: the
aspects a thorough, well-researched answer must address, each with the
sub-points it includes. Write the final list from them, in the same two
layers.

- Keep everything a thorough answer to this question needs, even when only
  one draft names it; merge aspects or sub-points that name the same thing.
- Drop what is about the report rather than its subject (scope, method,
  introduction, instructions for writing, etc.), and what falls outside the
  question.
- 4 to 6 aspects, each a short noun phrase (at most 8 words); no two
  overlap. Each has 2 to 4 sub-points naming one thing each (at most 10
  words): the parts a good answer covers, not particular facts it may or
  may not find.

Return ONLY JSON:
{"aspects": [{"aspect": "...", "sub_points": ["...", "..."]}]}

@user

Question: {question}

Drafts:
{drafts}
