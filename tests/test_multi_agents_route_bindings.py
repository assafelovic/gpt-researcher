"""Regression test for #2060: ChiefEditorAgent and EditorAgent must bind
_route_fact_check / _route_draft_review to the free functions in
fact_review.py / draft_review.py, not merely reference them.

Before the fix, add_conditional_edges looked up self._route_fact_check /
self._route_draft_review at graph-construction time and raised
AttributeError, so multi_agents never started.

This imports both modules for real. The original version of this test
stubbed multi_agents.agents into sys.modules to route around the
import-time NameError in gpt_researcher/actions/query_processing.py, but
that fix ships in this same change, and the stubs leaked into sys.modules
and broke collection of tests/test_new_agents.py.
"""
from multi_agents.agents import orchestrator as orchestrator_mod
from multi_agents.agents import editor as editor_mod


class _FakeSubAgent:
    """Stands in for a real agent instance inside _create_workflow: any
    node/edge callable StateGraph asks for just needs to exist and be
    callable, it is never invoked in this test."""

    def __getattr__(self, item):
        async def _noop(*args, **kwargs):
            return {}

        return _noop


def _fake_agents():
    return {
        name: _FakeSubAgent()
        for name in ("writer", "editor", "research", "publisher", "human", "fact_checker", "visualizer")
    }


def test_route_fact_check_is_bound_and_delegates():
    chief = orchestrator_mod.ChiefEditorAgent.__new__(orchestrator_mod.ChiefEditorAgent)
    chief.task = {}
    assert chief._route_fact_check({"fact_check_notes": None}) == "accept"


def test_route_fact_check_respects_task_override():
    chief = orchestrator_mod.ChiefEditorAgent.__new__(orchestrator_mod.ChiefEditorAgent)
    chief.task = {"max_fact_check_revisions": 2}
    assert chief._route_fact_check(
        {"fact_check_notes": "fix X", "fact_check_revision_count": 2}
    ) == "revise"


def test_chief_editor_agent_create_workflow_does_not_crash():
    """The exact repro from #2060: building the graph used to raise
    AttributeError: 'ChiefEditorAgent' object has no attribute
    '_route_fact_check' before self._route_fact_check was ever called."""
    chief = orchestrator_mod.ChiefEditorAgent.__new__(orchestrator_mod.ChiefEditorAgent)
    chief.task = {}
    workflow = chief._create_workflow(_fake_agents())
    assert workflow is not None


def test_route_draft_review_is_bound_and_delegates():
    editor = editor_mod.EditorAgent()
    assert editor._route_draft_review({"review": None, "task": {}}) == "accept"


def test_route_draft_review_respects_task_override():
    editor = editor_mod.EditorAgent()
    draft = {
        "review": "fix sources",
        "draft_revision_count": 2,
        "task": {"max_draft_revisions": 2},
    }
    assert editor._route_draft_review(draft) == "revise"


def test_editor_agent_create_workflow_does_not_crash():
    """The exact repro from #2060 for the editor's own reviewer loop:
    AttributeError: 'EditorAgent' object has no attribute
    '_route_draft_review' before self._route_draft_review was ever called."""
    editor = editor_mod.EditorAgent()
    workflow = editor._create_workflow()
    assert workflow is not None
