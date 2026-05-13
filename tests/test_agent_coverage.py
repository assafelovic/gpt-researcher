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
