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
