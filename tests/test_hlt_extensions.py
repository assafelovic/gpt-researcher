import json
from pathlib import Path
import sys
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from backend.report_type.basic_report import basic_report
from backend.report_type.detailed_report import detailed_report
from backend.server import hlt_extensions


HLT_ENV_KEYS = [
    "KATAILYST_MCP_URL",
    "KATAILYST_MCP_TOKEN",
    "KATAILYST_AUTH_TOKEN",
    "GITHUB_MCP_URL",
    "GITHUB_MCP_TOKEN",
    "METABASE_MCP_URL",
    "METABASE_MCP_TOKEN",
    "FIRECRAWL_API_KEY",
    "FIRECRAWL_SERVER_URL",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_BASE_URL",
    "LANGFUSE_HOST",
    "LANGFUSE_RECORD_IO",
    "AI_SDK_TELEMETRY_RECORD_IO",
]


def clear_hlt_env(monkeypatch):
    for key in HLT_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def set_firecrawl_import(monkeypatch, available: bool):
    monkeypatch.setattr(
        hlt_extensions.importlib.util,
        "find_spec",
        lambda name: object() if available and name == "firecrawl" else None,
    )


def test_scope_resolution_degrades_without_env(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)

    task, mcp_enabled, mcp_strategy, configs, metadata, scraper_override = (
        hlt_extensions.prepare_research_request(
            task="Research the code and metrics",
            mcp_enabled=False,
            mcp_strategy="fast",
            mcp_configs=[],
            research_scope={
                "codebase": True,
                "cms": False,
                "metrics": True,
                "firecrawl": True,
                "depth": "balanced",
            },
        )
    )

    assert mcp_enabled is False
    assert mcp_strategy == "deep"
    assert configs == []
    assert scraper_override is None
    assert metadata["active_sources"] == []
    assert set(metadata["degraded_sources"]) == {"codebase", "metrics", "firecrawl"}
    assert metadata["scope_statuses"]["codebase"]["status"] == "unavailable"
    assert metadata["scraper"]["selected"] == "default"
    assert "do not imply unavailable internal data" in task


def test_scope_resolution_uses_configured_backends(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, True)
    monkeypatch.setenv("KATAILYST_MCP_TOKEN", "kata-secret")
    monkeypatch.setenv("GITHUB_MCP_URL", "https://github.example/mcp")
    monkeypatch.setenv("GITHUB_MCP_TOKEN", "github-secret")
    monkeypatch.setenv("METABASE_MCP_URL", "https://metabase.example/mcp")
    monkeypatch.setenv("METABASE_MCP_TOKEN", "metabase-secret")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fire-secret")

    _, mcp_enabled, _, configs, metadata, scraper_override = (
        hlt_extensions.prepare_research_request(
            task="Research the code and metrics",
            mcp_enabled=False,
            mcp_strategy="fast",
            mcp_configs=[],
            research_scope={
                "codebase": True,
                "cms": False,
                "metrics": True,
                "firecrawl": True,
                "depth": "deep",
            },
        )
    )

    assert mcp_enabled is True
    assert [config["name"] for config in configs] == ["katailyst", "github", "metabase"]
    assert scraper_override == "firecrawl"
    assert set(metadata["active_sources"]) == {"codebase", "metrics", "firecrawl"}
    assert metadata["degraded_sources"] == []
    assert "kata-secret" not in json.dumps(metadata)
    assert "github-secret" not in json.dumps(metadata)
    assert "metabase-secret" not in json.dumps(metadata)
    assert "fire-secret" not in json.dumps(metadata)


def test_codebase_scope_partial_with_only_katailyst(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    monkeypatch.setenv("KATAILYST_MCP_TOKEN", "kata-secret")

    _, mcp_enabled, _, configs, metadata, _ = hlt_extensions.prepare_research_request(
        task="Research implementation",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"codebase": True, "depth": "balanced"},
    )

    assert mcp_enabled is True
    assert [config["name"] for config in configs] == ["katailyst"]
    assert metadata["scope_statuses"]["codebase"]["status"] == "partial"
    assert metadata["active_sources"] == ["codebase"]
    assert metadata["degraded_sources"] == ["codebase"]


def test_metrics_scope_uses_katailyst_fallback_without_metabase(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    monkeypatch.setenv("KATAILYST_MCP_URL", "https://katailyst.example/mcp")
    monkeypatch.setenv("KATAILYST_MCP_TOKEN", "kata-secret")

    _, mcp_enabled, _, configs, metadata, _ = hlt_extensions.prepare_research_request(
        task="Research metrics",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"metrics": True, "depth": "balanced"},
    )

    assert mcp_enabled is True
    assert [config["name"] for config in configs] == ["metabase"]
    assert configs[0]["connection_url"] == "https://katailyst.example/mcp"
    assert metadata["scope_statuses"]["metrics"]["status"] == "ready"
    assert metadata["scope_statuses"]["metrics"]["components"]["katailyst_metrics_fallback"] == "ready"
    assert metadata["active_sources"] == ["metrics"]
    assert metadata["degraded_sources"] == []
    assert "kata-secret" not in json.dumps(metadata)


class FakeGPTResearcher:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.cfg = SimpleNamespace(scraper="bs", max_search_results_per_query=5)
        self.mcp_configs = kwargs.get("mcp_configs")
        self.mcp_strategy = kwargs.get("mcp_strategy")
        self.agent = None
        self.role = None


def test_basic_report_applies_scraper_override(monkeypatch):
    monkeypatch.setattr(basic_report, "GPTResearcher", FakeGPTResearcher)

    report = basic_report.BasicReport(
        query="test",
        query_domains=[],
        report_type="research_report",
        report_source="web",
        source_urls=[],
        document_urls=[],
        tone="Objective",
        config_path="default",
        websocket=None,
        scraper_override="firecrawl",
    )

    assert report.gpt_researcher.cfg.scraper == "firecrawl"


def test_detailed_report_applies_scraper_override(monkeypatch):
    monkeypatch.setattr(detailed_report, "GPTResearcher", FakeGPTResearcher)

    report = detailed_report.DetailedReport(
        query="test",
        report_type="detailed_report",
        report_source="web",
        tone="Objective",
        scraper_override="firecrawl",
    )

    assert report.gpt_researcher.cfg.scraper == "firecrawl"


def test_hlt_readiness_routes_are_sanitized_and_authenticated(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, True)
    monkeypatch.setenv("API_AUTH_KEY", "api-secret")
    monkeypatch.setenv("METABASE_MCP_URL", "https://metabase.example/mcp")
    monkeypatch.setenv("METABASE_MCP_TOKEN", "metabase-secret")

    app = FastAPI()
    hlt_extensions.install(app)
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    health_body = health.json()
    assert health_body["integrations"]["status"] in {"partial", "needs_config"}
    assert health_body["observability"]["langfuse"]["configured"] is False
    assert "api-secret" not in json.dumps(health_body)

    unauthorized = client.get("/api/hlt/readiness")
    assert unauthorized.status_code == 401

    readiness = client.get("/api/hlt/readiness", headers={"X-API-Key": "api-secret"})
    assert readiness.status_code == 200
    body = readiness.json()
    assert body["integrations"]["metrics"]["status"] == "ready"
    assert "metabase-secret" not in json.dumps(body)


def test_langfuse_health_status_is_redacted(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")
    monkeypatch.setenv("LANGFUSE_RECORD_IO", "true")

    app = FastAPI()
    hlt_extensions.install(app)
    client = TestClient(app)

    health = client.get("/health")

    assert health.status_code == 200
    body = health.json()
    langfuse = body["observability"]["langfuse"]
    assert langfuse["configured"] is True
    assert langfuse["public_key"] is True
    assert langfuse["secret_key"] is True
    assert langfuse["record_io"] is True
    assert langfuse["base_url"] == "https://us.cloud.langfuse.com"
    assert "pk-test" not in json.dumps(body)
    assert "sk-test" not in json.dumps(body)
