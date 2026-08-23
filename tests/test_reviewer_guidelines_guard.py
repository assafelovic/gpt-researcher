"""ReviewerAgent.review_draft must tolerate missing/None guidelines."""
import asyncio
import importlib.util
import pathlib
import sys
import types
from unittest.mock import AsyncMock, patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Load reviewer with light stubs for utils it imports at module level
pkg = types.ModuleType("multi_agents")
pkg.__path__ = [str(ROOT / "multi_agents")]
sys.modules.setdefault("multi_agents", pkg)
agents = types.ModuleType("multi_agents.agents")
agents.__path__ = [str(ROOT / "multi_agents" / "agents")]
sys.modules.setdefault("multi_agents.agents", agents)
utils = types.ModuleType("multi_agents.agents.utils")
utils.__path__ = [str(ROOT / "multi_agents" / "agents" / "utils")]
sys.modules.setdefault("multi_agents.agents.utils", utils)

# Ensure real none_sentinels can load
ns_path = ROOT / "multi_agents/agents/utils/none_sentinels.py"
ns_spec = importlib.util.spec_from_file_location(
    "multi_agents.agents.utils.none_sentinels", ns_path
)
ns_mod = importlib.util.module_from_spec(ns_spec)
sys.modules[ns_spec.name] = ns_mod
ns_spec.loader.exec_module(ns_mod)

views = types.ModuleType("multi_agents.agents.utils.views")
views.print_agent_output = lambda *a, **k: None
sys.modules["multi_agents.agents.utils.views"] = views
llms = types.ModuleType("multi_agents.agents.utils.llms")
llms.call_model = AsyncMock(return_value="looks fine")
sys.modules["multi_agents.agents.utils.llms"] = llms

path = ROOT / "multi_agents/agents/reviewer.py"
spec = importlib.util.spec_from_file_location("multi_agents.agents.reviewer", path)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
ReviewerAgent = mod.ReviewerAgent


def test_review_draft_none_guidelines_does_not_typeerror():
    agent = ReviewerAgent()
    state = {"task": {"guidelines": None, "model": "gpt-test"}, "draft": "body"}
    out = asyncio.run(agent.review_draft(state))
    assert out == "looks fine"
    # Prompt was built without crashing; join on None would have raised


def test_review_draft_missing_task_dict():
    agent = ReviewerAgent()
    # task missing entirely
    state = {"draft": "body"}
    out = asyncio.run(agent.review_draft(state))
    assert out == "looks fine"
