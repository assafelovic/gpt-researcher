# Question set

`questions_v0.jsonl` is a **placeholder** to exercise the pipeline end to end;
the real set's size and composition are still open (eval-design/README.md, 待定).
Bump the file version whenever questions change: the version is recorded in
every run archive.

Each line: `question_id`, `question`, `report_type`, and the `modes` to run it
in (`default`, `detailed`, `deep`).

`key_points/<question_id>.json` (optional) freezes a question's key points
after human review: `{"key_points": ["...", "..."]}`. When present it is used
instead of the cached judge output.

`key_points/q001.json` holds the 8 key points from the first judge-generated list
(the one the v0 seed scores used), reviewed by Sean on 2026-10-30. The UK item
stays: the question says Europe, not the EU. Without a frozen file, re-scoring
without the cache regenerated the list (7 points in one rep) and moved
comprehensiveness and decomposition coverage by up to 0.29 between reps.

`key_points/q002.json`–`q005.json` freeze the judge-generated lists (judge
gpt-6-luna, prompt v1) used in the 2026-10-31 five-question scores, so later
re-scores compare against the same points. Not yet reviewed item by item.
