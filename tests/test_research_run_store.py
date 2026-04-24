import sqlite3

from gpt_researcher.research_run_store import (
    INTERRUPTED_ERROR_CODE,
    ResearchRunStore,
)


def test_research_run_store_migrates_and_round_trips_json(tmp_path):
    db_path = tmp_path / "runs.sqlite3"
    store = ResearchRunStore(db_path)

    with sqlite3.connect(db_path) as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert version == 2

    store.create_run(
        "run-1",
        query="durable research",
        report_type="research_report",
        report_source="web",
        tone="Objective",
        resource_topic="durable research",
        hlt_research_scope={"active_sources": ["codebase"]},
    )
    store.complete_run(
        "run-1",
        context=[{"finding": "sqlite survives restart"}],
        sources=[{"title": "Source", "url": "https://example.com", "content": "abc"}],
        source_urls=["https://example.com"],
        costs=0.12,
        report_path="outputs/run-1.md",
        md_path="outputs/run-1.md",
        hlt_research_scope={"active_sources": ["codebase"], "degraded_sources": []},
    )

    reopened = ResearchRunStore(db_path)
    run = reopened.get_run("run-1")

    assert run["status"] == "completed"
    assert run["context"] == [{"finding": "sqlite survives restart"}]
    assert run["sources"][0]["title"] == "Source"
    assert run["source_urls"] == ["https://example.com"]
    assert run["source_count"] == 1
    assert run["costs"] == 0.12
    assert run["hlt_research_scope"]["active_sources"] == ["codebase"]
    assert reopened.get_run_by_resource_topic("durable research")["research_id"] == "run-1"


def test_research_run_store_marks_running_rows_interrupted_on_startup(tmp_path):
    db_path = tmp_path / "runs.sqlite3"
    store = ResearchRunStore(db_path, recover_interrupted=False)
    store.create_run("run-2", query="unfinished", status="running")

    recovered = ResearchRunStore(db_path, recover_interrupted=True)
    run = recovered.get_run("run-2")

    assert run["status"] == "failed"
    assert run["error_code"] == INTERRUPTED_ERROR_CODE
    assert "restart" in run["error_message"]
