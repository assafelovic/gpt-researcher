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
    "KATAILYST2_MCP_URL",
    "KATAILYST2_MCP_TOKEN",
    "HLT_CODEBASE_REPOS",
    "GITHUB_MCP_URL",
    "GITHUB_MCP_TOKEN",
    "CODEGRAPH_MCP_URL",
    "CODEGRAPH_MCP_TOKEN",
    "METABASE_MCP_URL",
    "METABASE_MCP_TOKEN",
    "LINEAR_API_KEY",
    "LINEAR_MCP_URL",
    "FIRECRAWL_API_KEY",
    "FIRECRAWL_SERVER_URL",
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
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


def test_katailyst_preset_defaults_to_katailyst2_url(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    monkeypatch.setenv("KATAILYST_MCP_TOKEN", "kata-secret")

    _, _, _, configs, _, _ = hlt_extensions.prepare_research_request(
        task="Research implementation",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"codebase": True, "depth": "balanced"},
    )

    assert configs[0]["connection_url"] == "https://katailyst2.vercel.app/mcp"


def test_katailyst2_env_preferred_over_legacy(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    monkeypatch.setenv("KATAILYST_MCP_URL", "https://legacy.example/mcp")
    monkeypatch.setenv("KATAILYST_MCP_TOKEN", "legacy-token")
    monkeypatch.setenv("KATAILYST2_MCP_URL", "https://k2.example/mcp")
    monkeypatch.setenv("KATAILYST2_MCP_TOKEN", "kata_k2-token")

    _, _, _, configs, _, _ = hlt_extensions.prepare_research_request(
        task="Research implementation",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"codebase": True, "depth": "balanced"},
    )

    assert configs[0]["connection_url"] == "https://k2.example/mcp"
    assert configs[0]["connection_headers"] == {"Authorization": "Bearer kata_k2-token"}


def test_codebase_instruction_names_estate_repos(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    monkeypatch.setenv("KATAILYST2_MCP_TOKEN", "kata_k2-token")

    task, _, _, _, _, _ = hlt_extensions.prepare_research_request(
        task="How does the apply funnel work?",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"codebase": True, "depth": "deep"},
    )

    for repo in (
        "Awhitter/nursing-mastery",
        "Awhitter/ScraperVault",
        "Awhitter/katailyst2",
        "Awhitter/MMM2",
        "Awhitter/evidence-based-business",
    ):
        assert repo in task


def test_codebase_prefers_codegraph_over_github(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    monkeypatch.setenv("KATAILYST2_MCP_TOKEN", "kata_k2-token")
    monkeypatch.setenv("CODEGRAPH_MCP_URL", "https://codegraph.example/mcp")
    monkeypatch.setenv("CODEGRAPH_MCP_TOKEN", "cg-secret")
    monkeypatch.setenv("GITHUB_MCP_URL", "https://github.example/mcp")

    _, mcp_enabled, _, configs, metadata, _ = hlt_extensions.prepare_research_request(
        task="Can MMM2 generate video?",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"codebase": True, "depth": "deep"},
    )

    assert mcp_enabled is True
    names = {c.get("name") for c in configs}
    assert "codegraph" in names
    assert "github" not in names
    assert metadata["preset_statuses"]["codegraph"]["status"] == "ready"


def test_brain_endpoints_return_estate_payload(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    app = FastAPI()
    hlt_extensions.install(app)
    client = TestClient(app)

    repos = client.get("/api/brain/repos")
    assert repos.status_code == 200
    slugs = {r["slug"] for r in repos.json()["repos"]}
    assert {"mmm2", "katailyst2", "ebb", "scrapervault", "nursing-mastery"} <= slugs

    changelog = client.get("/api/brain/changelog")
    assert changelog.status_code == 200
    assert len(changelog.json()["entries"]) >= 1

    roadmap = client.get("/api/brain/roadmap")
    assert roadmap.status_code == 200
    assert "milestones" in roadmap.json()


def test_codebase_repos_env_override(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    monkeypatch.setenv("KATAILYST2_MCP_TOKEN", "kata_k2-token")
    monkeypatch.setenv("HLT_CODEBASE_REPOS", "Awhitter/custom-repo (only repo)")

    task, _, _, _, _, _ = hlt_extensions.prepare_research_request(
        task="How does the apply funnel work?",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"codebase": True, "depth": "deep"},
    )

    assert "Awhitter/custom-repo (only repo)" in task
    assert "Awhitter/MMM2" not in task


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


def test_media_scope_searches_cloudinary_without_leaking_secrets(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "hlt-media")
    monkeypatch.setenv("CLOUDINARY_API_KEY", "cloudinary-key")
    monkeypatch.setenv("CLOUDINARY_API_SECRET", "cloudinary-secret")

    monkeypatch.setattr(
        hlt_extensions,
        "_cloudinary_list_assets",
        lambda: (
            [
                {
                    "public_id": "katailyst/ai-trends-hero",
                    "resource_type": "image",
                    "format": "png",
                    "asset_folder": "katailyst",
                    "secure_url": "https://res.cloudinary.com/hlt-media/image/upload/katailyst/ai-trends-hero.png",
                    "tags": ["katailyst", "ai"],
                },
                {
                    "public_id": "unrelated/archive",
                    "resource_type": "image",
                    "secure_url": "https://res.cloudinary.com/hlt-media/image/upload/unrelated/archive.png",
                },
            ],
            [],
        ),
    )

    task, mcp_enabled, _, configs, metadata, _ = hlt_extensions.prepare_research_request(
        task="Find AI trends for Katailyst",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"media": True, "depth": "balanced"},
    )

    assert mcp_enabled is False
    assert configs == []
    assert metadata["scope_statuses"]["media"]["status"] == "ready"
    assert metadata["active_sources"] == ["media"]
    assert metadata["media"]["searched"] is True
    assert metadata["media"]["asset_count"] == 1
    assert metadata["media"]["assets"][0]["public_id"] == "katailyst/ai-trends-hero"
    assert "Cloudinary media library context" in task
    assert "katailyst/ai-trends-hero" in task
    assert "cloudinary-key" not in json.dumps(metadata)
    assert "cloudinary-secret" not in json.dumps(metadata)


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
