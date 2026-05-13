from types import SimpleNamespace

import pytest

from gpt_researcher.actions import reasoning_critic, report_generation
from gpt_researcher.config import Config


@pytest.mark.asyncio
async def test_generate_report_appends_reasoning_critic_and_stores_bundle(monkeypatch):
    calls: list[str] = []

    async def fake_create_chat_completion(**kwargs):
        prompt_text = "\n".join(message.get("content", "") for message in kwargs.get("messages", []))
        calls.append(prompt_text)

        if "Translate the following markdown report into German" in prompt_text:
            return """# Vergleiche FastAPI und Flask für asynchrone Python-APIs

## Überblick
FastAPI ist für asynchrone APIs ausgelegt und validiert Daten mit Pydantic.

## Zentrale Erkenntnisse
- Flask bleibt ein kompaktes Microframework und kann mit Erweiterungen für asynchrone Unterstützung kombiniert werden.
- FastAPI wird häufig für typisierte Request-Validierung gewählt.

## Verifikationsprüfung
- Risikostufe: niedrig
- Manuelle Prüfung erforderlich: nein

## Begründungskritik
- Urteil: überarbeiten
"""

        if "skeptical senior research editor" in prompt_text or "VERIFICATION BUNDLE" in prompt_text:
            return """
            {
              "verdict": "revise",
              "confidence": 0.83,
              "summary": "One comparative claim is a little too strong.",
              "issues": [
                {
                  "severity": "medium",
                  "claim": "FastAPI is always faster than Flask.",
                  "problem": "The wording is absolute and not supported by the evidence bundle.",
                  "evidence": ["claim:1"],
                  "suggested_fix": "Qualify the statement and cite a direct benchmark."
                }
              ],
              "strengths": ["The report includes a verification appendix."],
              "recommendations": ["Soften absolute performance language."]
            }
            """

        return """# Compare FastAPI and Flask for async Python APIs

## Overview
FastAPI is designed for async-first APIs and validates data with Pydantic.

## Key Findings
- Flask remains a compact microframework and can be combined with extensions for async support.
- FastAPI is often chosen for typed request validation.
"""

    monkeypatch.setattr(report_generation, "create_chat_completion", fake_create_chat_completion)
    monkeypatch.setattr(reasoning_critic, "create_chat_completion", fake_create_chat_completion)

    cfg = Config()
    cfg.enable_verification_review = True
    cfg.enable_reasoning_critic = True

    sink = SimpleNamespace()

    report = await report_generation.generate_report(
        query="Compare FastAPI and Flask for async Python APIs",
        context="""
FastAPI is designed for async-first APIs and validates data with Pydantic.
https://fastapi.tiangolo.com/

Flask remains a compact microframework and can be combined with extensions for async support.
https://flask.palletsprojects.com/
""",
        agent_role_prompt="You are a meticulous research assistant.",
        report_type="research_report",
        tone=None,
        report_source="web",
        websocket=None,
        cfg=cfg,
        verification_sink=sink,
    )

    assert report.startswith("# Vergleiche FastAPI und Flask für asynchrone Python-APIs")
    assert "## Verifikationsprüfung" in report
    assert "## Begründungskritik" in report
    assert getattr(sink, "verification_bundle", None) is not None
    assert getattr(sink, "reasoning_critic_bundle", None) is not None
    assert sink.reasoning_critic_bundle["verdict"] == "revise"
    assert sink.verification_bundle["critic"]["verdict"] == "revise"
    assert any("skeptical senior research editor" in prompt for prompt in calls)
    assert any("Translate the following markdown report into German" in prompt for prompt in calls)


@pytest.mark.asyncio
async def test_reasoning_critic_falls_back_to_deterministic_bundle(monkeypatch):
    async def failing_create_chat_completion(**kwargs):
        raise RuntimeError("critic failed")

    monkeypatch.setattr(reasoning_critic, "create_chat_completion", failing_create_chat_completion)

    cfg = Config()
    cfg.enable_reasoning_critic = True

    verification_bundle = {
        "query": "What are the treatment options for diabetes?",
        "summary": {
            "claims_total": 1,
            "supported_claims": 0,
            "partial_claims": 0,
            "unsupported_claims": 1,
            "support_rate": 0.0,
            "source_count": 0,
        },
        "risk": {
            "level": "high",
            "human_review_required": True,
            "reason": "health: treatment",
        },
        "claims": [
            {
                "id": "claim:1",
                "claim": "Insulin is the only treatment.",
                "status": "unsupported",
                "confidence": 0.1,
                "sources": [],
            }
        ],
        "evidence_graph": {"nodes": [], "edges": []},
    }

    bundle = await reasoning_critic.build_reasoning_critic_bundle(
        query="What are the treatment options for diabetes?",
        context="Insulin and other therapies should be reviewed by a clinician.",
        report_markdown="# Report\n\n## Overview\nInsulin is the only treatment.",
        verification_bundle=verification_bundle,
        cfg=cfg,
        agent_role_prompt="You are a skeptical editor.",
        visited_urls=[],
    )

    assert bundle["source"] == "deterministic"
    assert bundle["verdict"] == "high_risk"
    assert bundle["issues"]


@pytest.mark.asyncio
async def test_reasoning_critic_localizes_default_llm_fallbacks(monkeypatch):
    calls: list[str] = []

    async def fake_create_chat_completion(**kwargs):
        prompt_text = "\n".join(message.get("content", "") for message in kwargs.get("messages", []))
        calls.append(prompt_text)
        return """
        {
          "verdict": "revise",
          "confidence": 0.83,
          "summary": "",
          "issues": [],
          "strengths": [],
          "recommendations": []
        }
        """

    monkeypatch.setattr(reasoning_critic, "create_chat_completion", fake_create_chat_completion)

    cfg = Config()
    cfg.enable_reasoning_critic = True

    bundle = await reasoning_critic.build_reasoning_critic_bundle(
        query="Compare FastAPI and Flask for async Python APIs",
        context="FastAPI and Flask have different async capabilities.",
        report_markdown="# Bericht\n\n## Überblick\nFastAPI ist asynchron.",
        verification_bundle={
            "query": "Compare FastAPI and Flask for async Python APIs",
            "summary": {
                "claims_total": 1,
                "supported_claims": 1,
                "partial_claims": 0,
                "unsupported_claims": 0,
                "support_rate": 1.0,
                "source_count": 1,
            },
            "risk": {
                "level": "low",
                "human_review_required": False,
                "reason": "general",
            },
            "claims": [],
            "evidence_graph": {"nodes": [], "edges": []},
        },
        cfg=cfg,
        agent_role_prompt="You are a skeptical editor.",
        language="german",
        visited_urls=[],
    )

    assert bundle["source"] == "llm"
    assert bundle["summary"] == "Der Begründungskritiker hat den Bericht und den Verifikationsanhang geprüft."
    assert any("Aussagen werden direkt durch das Evidenzpaket gestützt." in strength for strength in bundle["strengths"])
    assert any("Priorisieren Sie Aussagen" in recommendation for recommendation in bundle["recommendations"])
    assert any("Respond in German" in prompt for prompt in calls)


@pytest.mark.asyncio
async def test_reasoning_critic_strips_internal_metadata_from_llm_call(monkeypatch):
    captured = {}

    async def fake_create_chat_completion(**kwargs):
        captured.update(kwargs)
        return """
        {
          "verdict": "pass",
          "confidence": 0.91,
          "summary": "Looks good.",
          "issues": [],
          "strengths": ["The report is grounded in the evidence bundle."],
          "recommendations": []
        }
        """

    monkeypatch.setattr(reasoning_critic, "create_chat_completion", fake_create_chat_completion)

    cfg = Config()
    cfg.enable_reasoning_critic = True

    bundle = await reasoning_critic.build_reasoning_critic_bundle(
        query="Compare FastAPI and Flask for async Python APIs",
        context="FastAPI and Flask have different async capabilities.",
        report_markdown="# Report\n\n## Overview\nFastAPI is async-first.",
        verification_bundle={
            "query": "Compare FastAPI and Flask for async Python APIs",
            "summary": {
                "claims_total": 1,
                "supported_claims": 1,
                "partial_claims": 0,
                "unsupported_claims": 0,
                "support_rate": 1.0,
                "source_count": 1,
            },
            "risk": {
                "level": "low",
                "human_review_required": False,
                "reason": "general",
            },
            "claims": [],
            "evidence_graph": {"nodes": [], "edges": []},
        },
        cfg=cfg,
        agent_role_prompt="You are a skeptical editor.",
        visited_urls=["https://example.com/should-not-be-forwarded"],
    )

    assert bundle["source"] == "llm"
    assert "visited_urls" not in captured


def test_reasoning_critic_parses_code_fenced_payload_without_braces():
    response = """```json
verdict: revise
confidence: 0.83
summary: One comparative claim is a little too strong.
issues: []
strengths: ["The report includes a verification appendix."]
recommendations: ["Soften absolute performance language."]
```"""

    payload = reasoning_critic._parse_critic_payload(response)

    assert payload is not None
    assert payload["verdict"] == "revise"
    assert payload["confidence"] == 0.83


@pytest.mark.asyncio
async def test_reasoning_critic_parses_ansi_wrapped_code_fenced_payload_without_braces(monkeypatch):
    async def fake_create_chat_completion(**kwargs):
        return "\x1b[32m```json\n\x1b[0mbuce: \"no brand touchpoints or extras, no extras added\"\n\x1b[32m```\x1b[0m"

    monkeypatch.setattr(reasoning_critic, "create_chat_completion", fake_create_chat_completion)

    cfg = Config()
    cfg.enable_reasoning_critic = True

    bundle = await reasoning_critic.build_reasoning_critic_bundle(
        query="Compare FastAPI and Flask for async Python APIs",
        context="FastAPI and Flask have different async capabilities.",
        report_markdown="# Report\n\n## Overview\nFastAPI is async-first.",
        verification_bundle={
            "query": "Compare FastAPI and Flask for async Python APIs",
            "summary": {
                "claims_total": 1,
                "supported_claims": 1,
                "partial_claims": 0,
                "unsupported_claims": 0,
                "support_rate": 1.0,
                "source_count": 1,
            },
            "risk": {
                "level": "low",
                "human_review_required": False,
                "reason": "general",
            },
            "claims": [],
            "evidence_graph": {"nodes": [], "edges": []},
        },
        cfg=cfg,
        agent_role_prompt="You are a skeptical editor.",
        visited_urls=[],
    )

    assert bundle["source"] == "llm"
    assert bundle["verdict"] == "revise"
