"""Offline unit tests for optional per-run research cost budget guardrails.

Covers:
- Default unlimited behavior (backward compatibility)
- Config / environment parsing for MAX_RESEARCH_COST and instance override
- Input validation for invalid max_cost values
- Single-shot budget_exceeded event delivery to log_handler & research_observer
- Graceful convergence in ResearchConductor, DeepResearchSkill, and DetailedReport
- Budget propagation to nested deep-research and subtopic researchers
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import backend.report_type.detailed_report.detailed_report as detailed_report
import gpt_researcher
from gpt_researcher import GPTResearcher
from gpt_researcher.config import Config
from gpt_researcher.config.variables.default import DEFAULT_CONFIG
from gpt_researcher.skills.deep_research import DeepResearchSkill
from gpt_researcher.skills.researcher import ResearchConductor


class _RecordingLogHandler:
    def __init__(self):
        self.steps = []

    async def on_research_step(self, step, details):
        self.steps.append((step, details))


class _RecordingObserver:
    def __init__(self):
        self.events = []

    def on_event(self, event, **fields):
        self.events.append((event, fields))


def _bare_researcher(
    *,
    max_cost=None,
    research_costs=0.0,
    log_handler=None,
    research_observer=None,
):
    researcher = GPTResearcher.__new__(GPTResearcher)
    researcher.cfg = SimpleNamespace(
        max_research_cost=None,
        curate_sources=False,
        max_search_results_per_query=5,
        mcp_strategy="disabled",
    )
    researcher.query = "budget guardrail test"
    researcher.report_type = "research_report"
    researcher.report_source = "web"
    researcher.agent = "Agent"
    researcher.role = "Role"
    researcher.parent_query = ""
    researcher.subtopics = []
    researcher.source_urls = None
    researcher.document_urls = None
    researcher.complement_source_urls = False
    researcher.query_domains = []
    researcher.visited_urls = set()
    researcher.research_sources = []
    researcher.research_images = []
    researcher.available_images = []
    researcher.context = []
    researcher.headers = {}
    researcher.websocket = None
    researcher.verbose = False
    researcher.kwargs = {}
    researcher.retrievers = []
    researcher.mcp_configs = None
    researcher.mcp_strategy = "disabled"
    researcher.research_costs = research_costs
    researcher.step_costs = {}
    researcher._current_step = "research"
    researcher.log_handler = log_handler
    researcher.research_observer = research_observer
    researcher._budget_exceeded_notified = False
    researcher.max_cost = researcher._resolve_max_cost(max_cost)
    return researcher


def test_default_config_disables_cost_budget():
    assert DEFAULT_CONFIG["MAX_RESEARCH_COST"] is None
    cfg = Config()
    assert cfg.max_research_cost is None


def test_config_parses_max_research_cost_from_env(monkeypatch):
    monkeypatch.setenv("MAX_RESEARCH_COST", "0.25")
    cfg = Config()
    assert cfg.max_research_cost == pytest.approx(0.25)

    monkeypatch.setenv("MAX_RESEARCH_COST", "none")
    cfg_none = Config()
    assert cfg_none.max_research_cost is None


def test_resolve_max_cost_prefers_instance_over_config():
    researcher = _bare_researcher()
    researcher.cfg.max_research_cost = 0.50

    assert researcher._resolve_max_cost(None) == pytest.approx(0.50)
    assert researcher._resolve_max_cost(0.15) == pytest.approx(0.15)
    assert researcher._resolve_max_cost(0) == 0.0


@pytest.mark.parametrize(
    "bad_value",
    [-0.01, -5, float("nan"), float("inf"), float("-inf"), True, False, "0.5"],
)
def test_resolve_max_cost_rejects_invalid_values(bad_value):
    researcher = _bare_researcher()
    with pytest.raises(ValueError, match="max_cost"):
        researcher._resolve_max_cost(bad_value)


def test_init_accepts_max_cost_kwarg_without_leaking_to_llm_kwargs(monkeypatch):
    monkeypatch.setattr("gpt_researcher.agent.get_retrievers", lambda headers, cfg: [])
    researcher = GPTResearcher(query="budget init test", max_cost=0.35, verbose=False)

    assert researcher.max_cost == pytest.approx(0.35)
    assert "max_cost" not in researcher.kwargs
    assert researcher.get_remaining_budget() == pytest.approx(0.35)


def test_uninitialized_researcher_has_no_budget_limit():
    """Callers using GPTResearcher.__new__ (as in existing unit tests) stay compatible."""
    researcher = GPTResearcher.__new__(GPTResearcher)
    researcher.research_costs = 1.25
    researcher.step_costs = {}
    researcher._current_step = "research"
    researcher.log_handler = None

    assert researcher.is_budget_exceeded() is False
    assert researcher.get_remaining_budget() is None
    researcher.add_costs(0.5)
    assert researcher.get_costs() == pytest.approx(1.75)


def test_budget_helpers_and_sync_add_costs():
    researcher = _bare_researcher(max_cost=0.10)

    assert researcher.is_budget_exceeded() is False
    assert researcher.get_remaining_budget() == pytest.approx(0.10)

    researcher.add_costs(0.04)
    assert researcher.is_budget_exceeded() is False
    assert researcher.get_remaining_budget() == pytest.approx(0.06)

    researcher.add_costs(0.08)
    assert researcher.is_budget_exceeded() is True
    assert researcher.get_remaining_budget() == 0.0


async def test_budget_exceeded_event_fires_once_for_handler_and_observer():
    handler = _RecordingLogHandler()
    observer = _RecordingObserver()
    researcher = _bare_researcher(
        max_cost=0.10,
        log_handler=handler,
        research_observer=observer,
    )

    researcher.add_costs(0.05)
    researcher.add_costs(0.05)
    researcher.add_costs(0.02)
    await asyncio.sleep(0)

    budget_steps = [details for step, details in handler.steps if step == "budget_exceeded"]
    budget_events = [fields for event, fields in observer.events if event == "budget_exceeded"]

    assert len(budget_steps) == 1
    assert budget_steps[0]["max_cost"] == pytest.approx(0.10)
    assert budget_steps[0]["total_cost"] == pytest.approx(0.10)

    assert len(budget_events) == 1
    assert budget_events[0]["max_cost"] == pytest.approx(0.10)
    assert budget_events[0]["total_cost"] == pytest.approx(0.10)
    assert budget_events[0]["step_name"] == "research"


async def test_web_search_skips_immediately_when_budget_exhausted():
    researcher = _bare_researcher(max_cost=0.05, research_costs=0.05)
    conductor = ResearchConductor(researcher)
    conductor._get_initial_search_results = AsyncMock()
    conductor.plan_research = AsyncMock()

    result = await conductor._get_context_by_web_search("test query")

    assert result == []
    conductor._get_initial_search_results.assert_not_awaited()
    conductor.plan_research.assert_not_awaited()


async def test_web_search_converges_after_planning_exhausts_budget():
    researcher = _bare_researcher(max_cost=0.05)
    conductor = ResearchConductor(researcher)
    conductor._get_initial_search_results = AsyncMock(
        return_value=[{"href": "https://example.com/a", "body": "snippet"}]
    )

    async def expensive_plan(*args, **kwargs):
        researcher.add_costs(0.06)
        return ["sub-query-1", "sub-query-2"]

    conductor.plan_research = AsyncMock(side_effect=expensive_plan)
    conductor._process_sub_query = AsyncMock(return_value="should not run")

    result = await conductor._get_context_by_web_search("test query")

    assert result == []
    conductor._process_sub_query.assert_not_awaited()


async def test_process_sub_query_returns_empty_when_budget_exceeded():
    researcher = _bare_researcher(max_cost=0.01, research_costs=0.02)
    conductor = ResearchConductor(researcher)
    conductor._scrape_data_by_urls = AsyncMock()

    result = await conductor._process_sub_query("sub-query")

    assert result == ""
    conductor._scrape_data_by_urls.assert_not_awaited()


async def test_conduct_research_skips_complement_curation_and_images_when_over_budget():
    researcher = _bare_researcher(max_cost=0.05)
    researcher.source_urls = ["https://example.com/source"]
    researcher.complement_source_urls = True
    researcher.cfg.curate_sources = True
    researcher.source_curator = SimpleNamespace(curate_sources=AsyncMock())
    researcher.image_generator = SimpleNamespace(
        is_enabled=MagicMock(return_value=True),
        plan_and_generate_images=AsyncMock(return_value=["img.png"]),
    )

    conductor = ResearchConductor(researcher)

    async def fake_context_by_urls(urls):
        researcher.add_costs(0.06)
        return "preserved context from source_urls"

    conductor._get_context_by_urls = AsyncMock(side_effect=fake_context_by_urls)
    conductor._get_context_by_web_search = AsyncMock(return_value="extra web context")
    researcher.research_conductor = conductor

    context = await researcher.conduct_research()

    assert context == "preserved context from source_urls"
    conductor._get_context_by_web_search.assert_not_awaited()
    researcher.source_curator.curate_sources.assert_not_awaited()
    researcher.image_generator.plan_and_generate_images.assert_not_awaited()
    assert researcher.available_images == []


async def test_deep_research_stops_before_query_generation_when_budget_exhausted():
    researcher = _bare_researcher(max_cost=0.10, research_costs=0.10)
    researcher.tone = "Objective"
    skill = DeepResearchSkill(researcher)
    skill.generate_search_queries = AsyncMock()

    result = await skill.deep_research(
        query="deep topic",
        breadth=2,
        depth=2,
        learnings=["existing learning"],
        visited_urls={"https://example.com/existing"},
    )

    skill.generate_search_queries.assert_not_awaited()
    assert result["learnings"] == ["existing learning"]
    assert result["visited_urls"] == {"https://example.com/existing"}


async def test_deep_research_propagates_remaining_budget_and_halts_recursion():
    researcher = _bare_researcher(max_cost=0.10, research_costs=0.02)
    researcher.tone = "Objective"
    skill = DeepResearchSkill(researcher)
    skill.concurrency_limit = 1

    skill.generate_search_queries = AsyncMock(
        return_value=[
            {"query": "branch-1", "researchGoal": "goal-1"},
            {"query": "branch-2", "researchGoal": "goal-2"},
        ]
    )
    skill.process_research_results = AsyncMock(
        return_value={
            "learnings": ["should not run after budget hit"],
            "followUpQuestions": ["follow-up?"],
            "citations": {},
        }
    )

    spawned_calls = []

    class _FakeChildResearcher:
        def __init__(self, **kwargs):
            spawned_calls.append(kwargs)
            self.visited_urls = {"https://example.com/branch-1"}
            self.research_sources = [{"url": "https://example.com/branch-1"}]

        async def conduct_research(self):
            return "collected branch-1 context"

        def get_costs(self):
            return 0.09

    with patch.object(gpt_researcher, "GPTResearcher", _FakeChildResearcher):
        result = await skill.deep_research(query="root", breadth=2, depth=2)

    # First child received remaining budget (0.08), exhausted parent budget (0.02 + 0.09 = 0.11),
    # so second branch, learning extraction, and depth-1 recursion were all skipped.
    assert len(spawned_calls) == 1
    assert spawned_calls[0]["max_cost"] == pytest.approx(0.08)
    skill.process_research_results.assert_not_awaited()
    assert researcher.is_budget_exceeded() is True
    assert "collected branch-1 context" in result["context"]
    assert "https://example.com/branch-1" in result["visited_urls"]


async def test_detailed_report_skips_subtopics_when_budget_exceeded_and_propagates_remaining():
    report = detailed_report.DetailedReport.__new__(detailed_report.DetailedReport)
    report.query = "main topic"
    report.query_domains = []
    report.report_source = "web"
    report.websocket = None
    report.headers = {}
    report.subtopics = []
    report.global_urls = set()
    report.tone = "Objective"
    report.complement_source_urls = False
    report.source_urls = []
    report.document_urls = []
    report.config_path = None
    report.max_search_results = None

    # Case 1: budget already exhausted -> skip all subtopics
    report.gpt_researcher = _bare_researcher(max_cost=0.10, research_costs=0.10)
    report._research_subtopic = AsyncMock()
    reports, body = await report._generate_subtopic_reports([{"task": "Subtopic A"}])
    assert reports == []
    assert body == ""
    report._research_subtopic.assert_not_awaited()

    # Case 2: remaining budget is propagated to subtopic GPTResearcher
    report.gpt_researcher = _bare_researcher(max_cost=0.25, research_costs=0.05)
    report.gpt_researcher.extract_headers = lambda text: []
    captured = {}

    class _FakeSubtopicResearcher:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.cfg = SimpleNamespace(max_search_results_per_query=5)

        async def conduct_research(self):
            return "subtopic context"

        async def get_draft_section_titles(self, task):
            return ["## Overview"]

    with patch.object(detailed_report, "GPTResearcher", _FakeSubtopicResearcher):
        await detailed_report.DetailedReport._research_subtopic(report, {"task": "Subtopic A"})

    assert captured["max_cost"] == pytest.approx(0.20)
