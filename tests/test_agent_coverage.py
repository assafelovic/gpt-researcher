import os
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

import pytest

from gpt_researcher.agent import GPTResearcher
from gpt_researcher.utils.enum import ReportType


class TestResolveMCPStrategy:
    def test_new_strategy_names_pass_through(self):
        researcher = GPTResearcher(query="test", report_type="research_report")
        assert researcher._resolve_mcp_strategy("fast", None) == "fast"
        assert researcher._resolve_mcp_strategy("deep", None) == "deep"
        assert researcher._resolve_mcp_strategy("disabled", None) == "disabled"

    def test_deprecated_optimized_maps_to_fast(self):
        researcher = GPTResearcher(query="test", report_type="research_report")
        assert researcher._resolve_mcp_strategy("optimized", None) == "fast"

    def test_deprecated_comprehensive_maps_to_deep(self):
        researcher = GPTResearcher(query="test", report_type="research_report")
        assert researcher._resolve_mcp_strategy("comprehensive", None) == "deep"

    def test_invalid_strategy_defaults_to_fast(self):
        researcher = GPTResearcher(query="test", report_type="research_report")
        assert researcher._resolve_mcp_strategy("invalid", None) == "fast"

    def test_mcp_max_iterations_zero_maps_to_disabled(self):
        researcher = GPTResearcher(query="test", report_type="research_report")
        assert researcher._resolve_mcp_strategy(None, 0) == "disabled"

    def test_mcp_max_iterations_one_maps_to_fast(self):
        researcher = GPTResearcher(query="test", report_type="research_report")
        assert researcher._resolve_mcp_strategy(None, 1) == "fast"

    def test_mcp_max_iterations_negative_one_maps_to_deep(self):
        researcher = GPTResearcher(query="test", report_type="research_report")
        assert researcher._resolve_mcp_strategy(None, -1) == "deep"

    def test_mcp_max_iterations_arbitrary_maps_to_fast(self):
        researcher = GPTResearcher(query="test", report_type="research_report")
        assert researcher._resolve_mcp_strategy(None, 5) == "fast"

    def test_config_strategy_fast(self):
        cfg = SimpleNamespace(mcp_strategy="fast")
        researcher = GPTResearcher(query="test", report_type="research_report")
        researcher.cfg = cfg
        assert researcher._resolve_mcp_strategy(None, None) == "fast"

    def test_config_strategy_deep(self):
        cfg = SimpleNamespace(mcp_strategy="deep")
        researcher = GPTResearcher(query="test", report_type="research_report")
        researcher.cfg = cfg
        assert researcher._resolve_mcp_strategy(None, None) == "deep"

    def test_config_strategy_disabled(self):
        cfg = SimpleNamespace(mcp_strategy="disabled")
        researcher = GPTResearcher(query="test", report_type="research_report")
        researcher.cfg = cfg
        assert researcher._resolve_mcp_strategy(None, None) == "disabled"

    def test_default_fast(self):
        cfg = SimpleNamespace()
        researcher = GPTResearcher(query="test", report_type="research_report")
        researcher.cfg = cfg
        assert researcher._resolve_mcp_strategy(None, None) == "fast"


class TestProcessMCPConfigs:
    def test_auto_adds_mcp_with_existing_retrievers(self):
        cfg = SimpleNamespace(retrievers="duckduckgo,google")
        researcher = GPTResearcher(query="test", report_type="research_report")
        researcher.cfg = cfg
        researcher._process_mcp_configs([{"name": "test-server"}])
        assert "mcp" in researcher.cfg.retrievers
        assert researcher.mcp_configs == [{"name": "test-server"}]

    def test_sets_mcp_as_default_when_no_retrievers(self):
        cfg = SimpleNamespace()
        researcher = GPTResearcher(query="test", report_type="research_report")
        researcher.cfg = cfg
        researcher._process_mcp_configs([{"name": "test-server"}])
        assert researcher.cfg.retrievers == "mcp"
        assert researcher.mcp_configs == [{"name": "test-server"}]

    def test_skips_mcp_when_user_explicitly_set_retriever(self):
        cfg = SimpleNamespace(retrievers="google")
        researcher = GPTResearcher(query="test", report_type="research_report")
        researcher.cfg = cfg
        researcher.cfg._explicit_env_keys = {"RETRIEVER"}
        researcher._process_mcp_configs([{"name": "test-server"}])
        assert researcher.cfg.retrievers == "google"

    def test_does_not_duplicate_mcp(self):
        cfg = SimpleNamespace(retrievers="duckduckgo,mcp")
        researcher = GPTResearcher(query="test", report_type="research_report")
        researcher.cfg = cfg
        researcher._process_mcp_configs([{"name": "test-server"}])
        assert researcher.cfg.retrievers == "duckduckgo,mcp"

    def test_empty_mcp_configs_still_stores(self):
        cfg = SimpleNamespace(retrievers="duckduckgo")
        researcher = GPTResearcher(query="test", report_type="research_report")
        researcher.cfg = cfg
        researcher._process_mcp_configs([])
        assert researcher.mcp_configs == []


class TestReportTypeSwitches:
    @patch("gpt_researcher.agent.DeepResearchSkill")
    def test_deep_research_creates_skill(self, MockDeepResearch):
        researcher = GPTResearcher(
            query="deep test",
            report_type=ReportType.DeepResearch.value,
        )
        MockDeepResearch.assert_called_once_with(researcher)
        assert researcher.deep_researcher is not None

    def test_default_report_type_no_deep_researcher(self):
        researcher = GPTResearcher(
            query="normal test",
            report_type=ReportType.ResearchReport.value,
        )
        assert researcher.deep_researcher is None


class TestGenerateResearchID:
    def test_id_generated_on_access(self):
        researcher = GPTResearcher(query="test query")
        assert researcher._research_id == ""
        rid = researcher._generate_research_id()
        assert rid.startswith("research_")
        assert len(rid) > 10
        assert researcher._research_id == rid

    def test_id_is_stable(self):
        researcher = GPTResearcher(query="test query")
        rid1 = researcher._generate_research_id()
        rid2 = researcher._generate_research_id()
        assert rid1 == rid2


class TestAddCosts:
    def test_adds_cost_to_current_step(self):
        researcher = GPTResearcher(query="test")
        researcher.add_costs(1.5)
        assert researcher.research_costs == 1.5
        assert researcher.step_costs.get("general") == 1.5

    def test_adds_cost_to_tracked_step(self):
        researcher = GPTResearcher(query="test")
        researcher._current_step = "research"
        researcher.add_costs(2.0)
        researcher.add_costs(0.5)
        assert researcher.research_costs == 2.5
        assert researcher.step_costs.get("research") == 2.5

    def test_invalid_type_raises_value_error(self):
        researcher = GPTResearcher(query="test")
        with pytest.raises(ValueError, match="Cost must be an integer or float"):
            researcher.add_costs("not-a-number")


class TestUtilityWrappers:
    def test_get_costs_returns_total(self):
        researcher = GPTResearcher(query="test")
        researcher.research_costs = 42.0
        assert researcher.get_costs() == 42.0

    def test_set_verbose(self):
        researcher = GPTResearcher(query="test")
        researcher.set_verbose(False)
        assert researcher.verbose is False
        researcher.set_verbose(True)
        assert researcher.verbose is True

    def test_get_source_urls(self):
        researcher = GPTResearcher(query="test")
        researcher.visited_urls = {"https://example.com/a", "https://example.com/b"}
        urls = researcher.get_source_urls()
        assert len(urls) == 2

    def test_get_research_context(self):
        researcher = GPTResearcher(query="test")
        researcher.context = ["ctx1", "ctx2"]
        assert researcher.get_research_context() == ["ctx1", "ctx2"]

    def test_get_step_costs(self):
        researcher = GPTResearcher(query="test")
        researcher.step_costs = {"research": 1.0, "writing": 2.0}
        assert researcher.get_step_costs() == {"research": 1.0, "writing": 2.0}

    def test_add_research_images(self):
        researcher = GPTResearcher(query="test")
        researcher.add_research_images([{"url": "img1.jpg"}])
        assert len(researcher.research_images) == 1

    def test_get_research_images(self):
        researcher = GPTResearcher(query="test")
        researcher.research_images = [{"url": f"img{i}.jpg"} for i in range(5)]
        assert len(researcher.get_research_images(top_k=3)) == 3
        assert len(researcher.get_research_images(top_k=10)) == 5

    def test_add_research_sources(self):
        researcher = GPTResearcher(query="test")
        researcher.add_research_sources([{"url": "https://example.com"}])
        assert len(researcher.research_sources) == 1

    def test_get_research_sources(self):
        researcher = GPTResearcher(query="test")
        researcher.research_sources = [{"url": "https://example.com"}]
        assert len(researcher.get_research_sources()) == 1


class TestSafetyModeInitialization:
    def test_default_safety_mode_is_transparent(self):
        researcher = GPTResearcher(query="test")
        assert researcher.safety_mode == "TRANSPARENT"

    def test_safety_decision_initially_none(self):
        researcher = GPTResearcher(query="test")
        assert researcher.safety_decision is None
