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
    "APIFY_TOKEN",
    "APIFY_API_TOKEN",
    "APIFY_MCP_URL",
    "QBANK_MCP_URL",
    "QBANK_MCP_TOKEN",
    "REPORT_STORE_PATH",
    "DOC_PATH",
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


def test_deep_web_scope_adds_apify_preset(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, True)
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fire-secret")
    monkeypatch.setenv("APIFY_TOKEN", "apify-secret")

    _, mcp_enabled, _, configs, metadata, scraper = hlt_extensions.prepare_research_request(
        task="Scrape competitor pricing pages",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"firecrawl": True, "depth": "deep"},
    )

    assert mcp_enabled is True
    assert scraper == "firecrawl"
    apify = next(c for c in configs if c.get("name") == "apify")
    assert apify["connection_url"] == "https://mcp.apify.com"
    assert apify["connection_headers"]["Authorization"] == "Bearer apify-secret"
    assert metadata["preset_statuses"]["apify"]["status"] == "ready"


def test_apify_preset_skipped_without_token(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, True)
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fire-secret")

    _, _, _, configs, metadata, _ = hlt_extensions.prepare_research_request(
        task="Scrape competitor pricing pages",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"firecrawl": True},
    )

    assert all(c.get("name") != "apify" for c in configs)
    assert metadata["preset_statuses"]["apify"]["status"] == "unavailable"
    assert "APIFY_TOKEN" in metadata["preset_statuses"]["apify"]["missing"]


def _mock_linear_graphql(monkeypatch, payload_by_query_marker):
    def fake_graphql(query, timeout=8):
        for marker, payload in payload_by_query_marker.items():
            if marker in query:
                return payload
        return None

    monkeypatch.setattr(hlt_extensions, "_linear_graphql", fake_graphql)
    hlt_extensions._linear_cache.clear()


def test_roadmap_uses_live_linear_projects(monkeypatch):
    clear_hlt_env(monkeypatch)
    monkeypatch.setenv("LINEAR_API_KEY", "lin_api_secret")
    _mock_linear_graphql(
        monkeypatch,
        {
            "projects(": {
                "projects": {
                    "nodes": [
                        {
                            "id": "p1",
                            "name": "Nurse funnel v2",
                            "description": "Rebuild apply funnel",
                            "state": "started",
                            "progress": 0.6,
                            "targetDate": "2026-09-01",
                            "url": "https://linear.app/x/p1",
                        },
                        {
                            "id": "p2",
                            "name": "Dead project",
                            "state": "canceled",
                            "progress": 0.1,
                        },
                    ]
                }
            }
        },
    )

    roadmap = hlt_extensions.get_brain_roadmap()

    assert roadmap["provider"] == "linear"
    assert roadmap["linear_configured"] is True
    titles = [m["title"] for m in roadmap["milestones"]]
    assert titles == ["Nurse funnel v2"]
    assert roadmap["milestones"][0]["progress"] == 0.6
    assert "lin_api_secret" not in json.dumps(roadmap)


def test_roadmap_falls_back_to_seed_when_linear_fails(monkeypatch):
    clear_hlt_env(monkeypatch)
    monkeypatch.setenv("LINEAR_API_KEY", "lin_api_secret")
    _mock_linear_graphql(monkeypatch, {})  # every query returns None

    roadmap = hlt_extensions.get_brain_roadmap()

    assert roadmap["provider"] == "seed"
    assert roadmap["linear_configured"] is True
    assert len(roadmap["milestones"]) >= 1


def test_changelog_prepends_linear_completions(monkeypatch):
    clear_hlt_env(monkeypatch)
    monkeypatch.setenv("LINEAR_API_KEY", "lin_api_secret")
    _mock_linear_graphql(
        monkeypatch,
        {
            "issues(": {
                "issues": {
                    "nodes": [
                        {
                            "id": "i1",
                            "identifier": "NUR-42",
                            "title": "Ship recruiter dashboard",
                            "url": "https://linear.app/x/NUR-42",
                            "completedAt": "2026-07-28T12:00:00.000Z",
                            "team": {"name": "Nursing Mastery"},
                            "project": {"name": "Recruiting"},
                        }
                    ]
                }
            }
        },
    )

    entries = hlt_extensions.get_brain_changelog()

    assert entries[0]["id"] == "linear-NUR-42"
    assert entries[0]["date"] == "2026-07-28"
    assert entries[0]["kind"] == "shipped"
    assert entries[0]["source"] == "linear"
    # Seed entries stay after the live feed.
    assert any(e["id"] == "upstream-sync-2026-07" for e in entries)


def test_changelog_seed_only_without_linear(monkeypatch):
    clear_hlt_env(monkeypatch)
    hlt_extensions._linear_cache.clear()

    entries = hlt_extensions.get_brain_changelog()

    assert all(e.get("source") != "linear" for e in entries)
    assert len(entries) >= 3


def _seed_corpus(tmp_path, subdir, name="seed.md", content="# Seed\nNurses say things."):
    corpus_dir = tmp_path / subdir
    corpus_dir.mkdir(parents=True, exist_ok=True)
    (corpus_dir / name).write_text(content, encoding="utf-8")
    return tmp_path


def test_audience_scope_injects_forum_instructions(monkeypatch, tmp_path):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, True)
    monkeypatch.setenv("DOC_PATH", str(_seed_corpus(tmp_path, "audience")))
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fire-secret")
    monkeypatch.setenv("APIFY_TOKEN", "apify-secret")

    task, mcp_enabled, _, configs, metadata, scraper = hlt_extensions.prepare_research_request(
        task="What do new grad nurses complain about most?",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"audience": True, "depth": "deep"},
    )

    assert metadata["scope_statuses"]["audience"]["status"] == "ready"
    assert "audience" in metadata["active_sources"]
    assert "r/nursing" in task
    assert "allnurses.com" in task
    assert "verbatim" in task
    # Audience scope mounts Apify for forum reach and scrapes via Firecrawl.
    assert mcp_enabled is True
    assert any(c.get("name") == "apify" for c in configs)
    assert scraper == "firecrawl"


def test_audience_scope_partial_with_scrapers_only(monkeypatch, tmp_path):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, True)
    monkeypatch.setenv("DOC_PATH", str(tmp_path))  # no corpus docs
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fire-secret")

    _, _, _, _, metadata, _ = hlt_extensions.prepare_research_request(
        task="What do nurses complain about?",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"audience": True},
    )

    status = metadata["scope_statuses"]["audience"]
    assert status["status"] == "partial"
    assert status["active"] is True
    assert status["degraded"] is True
    assert "my-docs/audience/*.md" in status["missing"]


def test_recruiting_scope_names_nursingmastery(monkeypatch, tmp_path):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, True)
    monkeypatch.setenv("DOC_PATH", str(_seed_corpus(tmp_path, "recruiting")))
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fire-secret")

    task, _, _, _, metadata, scraper = hlt_extensions.prepare_research_request(
        task="Where are our content gaps for new grad ICU jobs?",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"recruiting": True, "depth": "deep"},
    )

    assert metadata["scope_statuses"]["recruiting"]["status"] == "ready"
    assert "nursingmastery.com" in task
    assert scraper == "firecrawl"


def test_top1_mode_injects_doctrine(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)

    task, _, _, _, metadata, _ = hlt_extensions.prepare_research_request(
        task="Best referral program for nurse recruiting",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"mode": "top1"},
    )

    assert metadata["mode"] == "top1"
    assert "top-1% study" in task
    assert "misdiagnose their own success" in task
    assert "rhymes with our niche" in task


def test_standard_mode_leaves_task_untouched(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)

    task, _, _, _, metadata, _ = hlt_extensions.prepare_research_request(
        task="Plain question",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={},
    )

    assert metadata["mode"] == "standard"
    assert task == "Plain question"


def _seed_report_store(tmp_path, monkeypatch, reports):
    path = tmp_path / "reports.json"
    path.write_text(json.dumps(reports), encoding="utf-8")
    monkeypatch.setenv("REPORT_STORE_PATH", str(path))
    return path


def test_prior_research_is_injected_into_related_tasks(monkeypatch, tmp_path):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    _seed_report_store(
        tmp_path,
        monkeypatch,
        {
            "r1": {
                "id": "r1",
                "question": "How do travel nurse recruiters source candidates?",
                "answer": "Recruiters source candidates from staffing marketplaces and referrals." * 5,
                "timestamp": 1753000000000,
            },
            "r2": {
                "id": "r2",
                "question": "Totally unrelated question about kubernetes",
                "answer": "Cluster things.",
                "timestamp": 1753000000001,
            },
        },
    )

    task, _, _, _, metadata, _ = hlt_extensions.prepare_research_request(
        task="What channels do nurse recruiters use to source candidates?",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={},
    )

    assert [item["id"] for item in metadata["prior_research"]] == ["r1"]
    assert "Prior internal research" in task
    assert "travel nurse recruiters" in task
    # Memory can be disabled per-request.
    task_off, _, _, _, metadata_off, _ = hlt_extensions.prepare_research_request(
        task="What channels do nurse recruiters use to source candidates?",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"memory": False},
    )
    assert metadata_off["prior_research"] == []
    assert "Prior internal research" not in task_off


def test_qbank_scope_prefers_dedicated_preset(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    monkeypatch.setenv("KATAILYST2_MCP_TOKEN", "kata_k2-token")
    monkeypatch.setenv("QBANK_MCP_URL", "https://qbank.example/mcp")
    monkeypatch.setenv("QBANK_MCP_TOKEN", "qbank-secret")

    _, mcp_enabled, _, configs, metadata, _ = hlt_extensions.prepare_research_request(
        task="Which items still cite the 2020 AHA guideline?",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"qbank": True, "depth": "deep"},
    )

    assert mcp_enabled is True
    names = [c["name"] for c in configs]
    assert "katailyst" in names and "qbank" in names
    qbank = next(c for c in configs if c["name"] == "qbank")
    assert qbank["connection_url"] == "https://qbank.example/mcp"
    assert qbank["connection_headers"] == {"Authorization": "Bearer qbank-secret"}
    assert metadata["scope_statuses"]["qbank"]["status"] == "ready"
    assert metadata["scope_statuses"]["qbank"]["components"]["qbank_partner_api"] == "ready"
    assert "qbank-secret" not in json.dumps(metadata)


def test_qbank_scope_falls_back_to_katailyst(monkeypatch):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    monkeypatch.setenv("KATAILYST2_MCP_TOKEN", "kata_k2-token")

    _, _, _, configs, metadata, _ = hlt_extensions.prepare_research_request(
        task="Audit guideline freshness",
        mcp_enabled=False,
        mcp_strategy="fast",
        mcp_configs=[],
        research_scope={"qbank": True},
    )

    assert [c["name"] for c in configs] == ["katailyst"]
    assert metadata["scope_statuses"]["qbank"]["status"] == "ready"
    assert metadata["scope_statuses"]["qbank"]["components"]["qbank_partner_api"] == "unavailable"


def test_brain_audience_and_library_endpoints(monkeypatch, tmp_path):
    clear_hlt_env(monkeypatch)
    set_firecrawl_import(monkeypatch, False)
    monkeypatch.setenv(
        "DOC_PATH",
        str(_seed_corpus(tmp_path, "audience", name="quotes.md", content="# Quote bank\n> so burned out")),
    )
    _seed_report_store(
        tmp_path,
        monkeypatch,
        {
            "r1": {
                "id": "r1",
                "question": "Nurse recruiting funnels",
                "answer": "Funnels work like this.",
                "timestamp": 1753000000000,
            }
        },
    )

    app = FastAPI()
    hlt_extensions.install(app)
    client = TestClient(app)

    audience = client.get("/api/brain/audience")
    assert audience.status_code == 200
    body = audience.json()
    assert body["documents"][0]["id"] == "quotes"
    assert "burned out" in body["documents"][0]["content"]

    library = client.get("/api/brain/library")
    assert library.status_code == 200
    assert library.json()["total"] == 1
    assert library.json()["reports"][0]["question"] == "Nurse recruiting funnels"

    search = client.get("/api/brain/library", params={"q": "recruiting funnels"})
    assert search.status_code == 200
    assert search.json()["reports"][0]["id"] == "r1"

    empty = client.get("/api/brain/library", params={"q": "quantum chromodynamics"})
    assert empty.status_code == 200
    assert empty.json()["reports"] == []
