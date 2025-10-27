import json
from pathlib import Path

from gpt_researcher.agent import GPTResearcher
from gpt_researcher.planning import PlanManager


def test_plan_manager_usage_and_persistence(tmp_path):
    manager = PlanManager("sample query", token_limit=120, web_limit=2, cost_limit=1.0)
    manager.add_step("sample query", "Resolve the main question")
    for name, value in [("tokens", 40), ("web_calls", 2), ("cost", 0.5)]:
        manager.record_usage(name, value)
    trace = manager.get_trace()
    assert trace["budgets"]["web_calls"]["used"] == 2
    assert manager.should_halt(enforce=True) is True
    researcher = GPTResearcher(query="test plan trace", verbose=False)
    researcher.plan_trace_path = str(tmp_path / "traces")
    researcher.plan_manager.add_step("test plan trace", "Primary objective")
    saved = Path(researcher.persist_plan_trace())
    payload = json.loads(saved.read_text())
    assert payload["query"] == "test plan trace"
    assert payload["steps"][0]["query"] == "test plan trace"
