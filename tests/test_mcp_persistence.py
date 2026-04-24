import asyncio
from pathlib import Path

import gpt_researcher.research_run_store as run_store_module
import mcp_server.tools as mcp_tools


class FakeGPTResearcher:
    def __init__(self, query, report_type="research_report", report_source="web", tone=None, **kwargs):
        self.query = query
        self.report_type = report_type
        self.report_source = report_source
        self.tone = tone
        self.context = []
        self.research_sources = []
        self.visited_urls = set()
        self.costs = 0.0

    async def conduct_research(self):
        self.context = [{"finding": f"context for {self.query}"}]
        self.research_sources = [
            {
                "title": "Example",
                "url": "https://example.com/research",
                "content": "source body",
            }
        ]
        self.visited_urls = {"https://example.com/research"}
        self.costs = 0.25

    async def write_report(self, custom_prompt=""):
        return f"# Report for {self.query}\n\n{custom_prompt}\n\n{self.context}"

    def get_research_context(self):
        return self.context

    def get_research_sources(self):
        return self.research_sources

    def get_source_urls(self):
        return list(self.visited_urls)

    def get_costs(self):
        return self.costs


def _reset_store(monkeypatch, tmp_path):
    monkeypatch.setenv("RESEARCH_RUN_STORE_PATH", str(tmp_path / "runs.sqlite3"))
    monkeypatch.setenv("OUTPUTS_DIR", str(tmp_path / "outputs"))
    run_store_module._store = None
    mcp_tools.clear_hot_cache()


def test_mcp_deep_research_survives_hot_cache_loss(monkeypatch, tmp_path):
    _reset_store(monkeypatch, tmp_path)
    monkeypatch.setattr(mcp_tools, "GPTResearcher", FakeGPTResearcher)

    result = asyncio.run(mcp_tools.deep_research_tool("restart-safe research"))
    assert result["status"] == "success"
    research_id = result["research_id"]

    mcp_tools.clear_hot_cache()

    context = asyncio.run(mcp_tools.get_research_context_tool(research_id))
    sources = asyncio.run(mcp_tools.get_research_sources_tool(research_id))

    assert context["status"] == "success"
    assert context["context"] == [{"finding": "context for restart-safe research"}]
    assert sources["status"] == "success"
    assert sources["sources"][0]["url"] == "https://example.com/research"


def test_mcp_write_report_hydrates_from_sqlite_after_restart(monkeypatch, tmp_path):
    _reset_store(monkeypatch, tmp_path)
    monkeypatch.setattr(mcp_tools, "GPTResearcher", FakeGPTResearcher)

    result = asyncio.run(mcp_tools.deep_research_tool("write after restart"))
    research_id = result["research_id"]
    mcp_tools.clear_hot_cache()

    report = asyncio.run(mcp_tools.write_report_tool(research_id, "Use bullets."))

    assert report["status"] == "success"
    assert "write after restart" in report["report"]
    assert Path(report["md_path"]).exists()

    run = run_store_module.get_research_run_store().get_run(research_id)
    assert run["status"] == "completed"
    assert run["md_path"] == report["md_path"]
    assert run["sources"][0]["title"] == "Example"
