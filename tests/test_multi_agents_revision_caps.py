"""All three multi_agents review loops must actually bound themselves (#2062).

The plan loop was wired to an inline lambda reading `revisions_count`, a key
nothing in the codebase ever writes, so the cap could never fire no matter how
many revisions a human requested. The real router (plan_review.route_human_feedback)
reads `plan_revision_count`, which human.py does write, but was never wired in.

The routers signal "over the ceiling" by raising. Their own docstrings say the
graph edge should turn that into a force-accept rather than let the run die at
LangGraph's recursion_limit, so each binding method is checked for both halves:
it delegates below the ceiling, and it force-accepts above it.
"""
from multi_agents.agents.editor import EditorAgent
from multi_agents.agents.orchestrator import ChiefEditorAgent


def _chief(task=None):
    chief = ChiefEditorAgent.__new__(ChiefEditorAgent)
    chief.task = task or {}
    return chief


# --- plan / human loop -------------------------------------------------

def test_plan_loop_accepts_when_no_feedback():
    assert _chief()._route_human_feedback({"human_feedback": None}) == "accept"


def test_plan_loop_revises_below_the_ceiling():
    chief = _chief({"max_plan_revisions": 3})
    state = {"human_feedback": "add a section on costs", "plan_revision_count": 1}
    assert chief._route_human_feedback(state) == "revise"


def test_plan_loop_force_accepts_above_the_ceiling():
    # The regression: this used to loop forever, because the wired lambda
    # read `revisions_count` and nothing ever set it.
    chief = _chief({"max_plan_revisions": 3})
    state = {"human_feedback": "still not right", "plan_revision_count": 99}
    assert chief._route_human_feedback(state) == "accept"


def test_plan_loop_respects_opt_out():
    chief = _chief({"max_plan_revisions": None})
    state = {"human_feedback": "again", "plan_revision_count": 10_000}
    assert chief._route_human_feedback(state) == "revise"


def test_plan_loop_reads_the_key_human_agent_writes():
    # human.py writes plan_revision_count. If the router ever goes back to
    # reading a different key, the count is invisible and the cap silently dies.
    chief = _chief({"max_plan_revisions": 1})
    ignored = {"human_feedback": "x", "revisions_count": 99}
    assert chief._route_human_feedback(ignored) == "revise"


# --- fact-check loop ---------------------------------------------------

def test_fact_check_accepts_with_no_notes():
    assert _chief()._route_fact_check({"fact_check_notes": None}) == "accept"


def test_fact_check_revises_below_the_ceiling():
    chief = _chief({"max_fact_check_revisions": 3})
    assert chief._route_fact_check(
        {"fact_check_notes": "fix X", "fact_check_revision_count": 1}
    ) == "revise"


def test_fact_check_force_accepts_above_the_ceiling():
    chief = _chief({"max_fact_check_revisions": 2})
    assert chief._route_fact_check(
        {"fact_check_notes": "fix X", "fact_check_revision_count": 99}
    ) == "accept"


# --- draft review loop -------------------------------------------------

def test_draft_review_accepts_with_no_review():
    assert EditorAgent()._route_draft_review({"review": None, "task": {}}) == "accept"


def test_draft_review_revises_below_the_ceiling():
    draft = {"review": "cite sources", "draft_revision_count": 1,
             "task": {"max_draft_revisions": 3}}
    assert EditorAgent()._route_draft_review(draft) == "revise"


def test_draft_review_force_accepts_above_the_ceiling():
    draft = {"review": "cite sources", "draft_revision_count": 99,
             "task": {"max_draft_revisions": 2}}
    assert EditorAgent()._route_draft_review(draft) == "accept"
