# Clean base reports

Reports of the dataset with the errors that the retrieved material can confirm
fixed by hand. They are the starting point for planted-defect tests: a defect
planted in a clean place has a known effect.

- One folder per run: `report.md` (the fixed report) and `fixes.json` (one
  entry per fix: line in the original report, the old and new text, the reason
  and the material words it rests on).
- The source run is named by the folder; its archive supplies everything else
  (queries, material). Only `report.markdown` differs.
- Rule: fixes are found by reading the report against the material, without
  looking at any judge verdict, so the evaluator's scores before and after are
  an independent check. A fix deletes or rewrites what the material does not
  back, or corrects an attribution; it never adds content from outside the
  material.

| Folder | Source archive | Fixes |
|---|---|---|
| `q001_default` | `seeds/v0/q001_default/archive.json` (run `20261029T234054_q001_default_3fc58f`) | 12 |
