"""Regression test for #2060: ChiefEditorAgent/EditorAgent must bind
_route_fact_check/_route_draft_review to the free functions in
fact_review.py/draft_review.py, not just reference them as unbound names.

Importing multi_agents.agents.orchestrator/editor for real pulls in
gpt_researcher (via the package's ResearchAgent and editor.py's own
.utils.llms), which independently fails to import on this HEAD (already
filed as #2055, an unordered typing import unrelated to this fix). The
loader below stubs only the handful of sibling agent classes and the
call_model import that orchestrator.py/editor.py reference but this test
never exercises, and lets everything else (fact_review, draft_review,
memory.research, utils.views, utils.utils) import for real.
"""
import sys
import types
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _noop(*args, **kwargs):
    return {}


def _stub_class(name):
    return type(name, (), {
        "__init__": lambda self, *a, **kw: None,
        "__getattr__": lambda self, item: _noop,
    })


def _ensure_pkg(name, path):
    if name not in sys.modules:
        mod = types.ModuleType(name)
        mod.__path__ = [str(path)]
        sys.modules[name] = mod
    return sys.modules[name]


def _load_module(mod_name, rel_path):
    spec = importlib.util.spec_from_file_location(mod_name, REPO_ROOT / rel_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def _load_orchestrator_and_editor():
    _ensure_pkg("multi_agents", REPO_ROOT / "multi_agents")
    agents_pkg = _ensure_pkg("multi_agents.agents", REPO_ROOT / "multi_agents" / "agents")
    for name in (
        "WriterAgent", "EditorAgent", "PublisherAgent", "ResearchAgent",
        "HumanAgent", "FactCheckerAgent", "VisualizerAgent",
        "ReviewerAgent", "ReviserAgent",
    ):
        if not hasattr(agents_pkg, name):
            setattr(agents_pkg, name, _stub_class(name))

    utils_pkg = _ensure_pkg("multi_agents.agents.utils", REPO_ROOT / "multi_agents" / "agents" / "utils")
    if "multi_agents.agents.utils.llms" not in sys.modules:
        llms_stub = types.ModuleType("multi_agents.agents.utils.llms")

        async def call_model(*args, **kwargs):
            raise NotImplementedError("stubbed for import isolation, not exercised by this test")

        llms_stub.call_model = call_model
        sys.modules["multi_agents.agents.utils.llms"] = llms_stub
        utils_pkg.llms = llms_stub

    orchestrator = _load_module("multi_agents.agents.orchestrator", "multi_agents/agents/orchestrator.py")
    editor = _load_module("multi_agents.agents.editor", "multi_agents/agents/editor.py")
    return orchestrator, editor


orchestrator_mod, editor_mod = _load_orchestrator_and_editor()


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
