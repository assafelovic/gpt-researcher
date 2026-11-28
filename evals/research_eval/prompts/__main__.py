"""python -m evals.research_eval.prompts [--lock]: check (or record) versions.json."""

import sys

from . import LOCK, lock_problems, write_lock

if sys.argv[1:] == ["--lock"]:
    write_lock()
    print(f"wrote {LOCK}")
else:
    problems = lock_problems()
    print("\n".join(problems) or "every prompt matches versions.json")
    sys.exit(1 if problems else 0)
