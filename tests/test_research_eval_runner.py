"""Tests for evals/research_eval/runner.py and the score CLI (offline)."""

import json
from types import SimpleNamespace

from evals.research_eval import runner, score


def _fake_researcher():
    cfg = SimpleNamespace(context_filter="keyword", smart_llm_provider="openai", smart_llm_model="s",
                          fast_llm_provider="openai", fast_llm_model="f",
                          strategic_llm_provider="openai", strategic_llm_model="g",
                          embedding_provider="openai", embedding_model="e", max_iterations=3,
                          max_search_results_per_query=5, deep_research_breadth=3,
                          deep_research_depth=2)
    return SimpleNamespace(cfg=cfg, report_type="research_report", retrievers=[type("Tavily", (), {})])


async def test_run_one_writes_archive(monkeypatch, tmp_path):
    async def fake_research(question, mode):
        return _fake_researcher(), "# Title\n\nBody.\n"

    monkeypatch.setattr(runner, "_research", fake_research)
    q = {"question_id": "q9", "question": "what?", "modes": ["default"]}
    path = await runner.run_one(q, "default", dataset=tmp_path / "questions_v7.jsonl", runs_dir=tmp_path)
    data = json.loads(path.read_text())
    assert path.parent == tmp_path / "questions_v7"
    assert data["schema_version"] == "1.0"
    meta = data["meta"]
    assert meta["status"] == "ok" and meta["question_id"] == "q9"
    assert meta["dataset_version"] == "questions_v7"
    assert meta["config"]["mode"] == "default" and meta["config"]["breadth"] is None
    assert meta["config"]["worker_model"]["smart"] == "openai:s"
    assert set(meta["health"]) >= {"jev_fallback", "subquery_errors"}
    assert data["spans"][0]["name"] == "run" and data["report"]["markdown"].startswith("# Title")


async def test_failed_run_is_still_archived(monkeypatch, tmp_path):
    async def boom(question, mode):
        raise RuntimeError("search API down")

    monkeypatch.setattr(runner, "_research", boom)
    q = {"question_id": "q1", "question": "x"}
    path = await runner.run_one(q, "deep", dataset="questions_v0.jsonl", runs_dir=tmp_path)
    data = json.loads(path.read_text())
    assert data["meta"]["status"] == "error" and "search API down" in data["meta"]["error"]
    assert data["spans"][0]["status"] == "error"


async def test_score_cli_rules_only(monkeypatch, tmp_path, capsys):
    async def fake_research(question, mode):
        return _fake_researcher(), "# T\n\nNothing.\n"

    monkeypatch.setattr(runner, "_research", fake_research)
    path = await runner.run_one({"question_id": "q1", "question": "x"}, "default",
                                dataset="questions_v0.jsonl", runs_dir=tmp_path)
    rc = await score.main([str(path), "--rules-only", "--cache", str(tmp_path / "c.sqlite"),
                           "--results-dir", str(tmp_path / "results")])
    assert rc == 0
    out = capsys.readouterr().out
    assert "plan_adherence" in out and "query_relevance" not in out
    [result] = (tmp_path / "results").rglob("*.json")
    rec = json.loads(result.read_text())
    assert rec["judge_model"] is None
    assert set(rec["metrics"]) == {"subquery_redundancy", "plan_adherence", "source_diversity", "citation_utilization",
                                   "retrieval_overlap", "instruction_following", "citation_coverage",
                                   "fact_grounding"}
