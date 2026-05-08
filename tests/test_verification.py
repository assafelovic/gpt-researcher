from types import SimpleNamespace

import pytest

from gpt_researcher.actions import report_generation
from gpt_researcher.actions.verification import (
    build_verification_bundle,
    classify_risk,
    render_verification_section,
)
from gpt_researcher.config import Config


def test_build_verification_bundle_extracts_claims_and_evidence():
    query = "Compare FastAPI and Flask for async Python APIs"
    context = """
FastAPI is designed for async-first APIs and validates data with Pydantic.
https://fastapi.tiangolo.com/

Flask remains a compact microframework and can be combined with extensions for async support.
https://flask.palletsprojects.com/
"""
    report = """# Compare FastAPI and Flask for async Python APIs

## Overview
FastAPI is designed for async-first APIs and validates data with Pydantic.

## Key Findings
- Flask remains a compact microframework and can be combined with extensions for async support.
- FastAPI is often chosen for typed request validation.
"""

    bundle = build_verification_bundle(
        query=query,
        context=context,
        report_markdown=report,
        visited_urls=[
            "https://fastapi.tiangolo.com/",
            "https://flask.palletsprojects.com/",
        ],
    )

    assert bundle["summary"]["claims_total"] >= 2
    assert bundle["summary"]["source_count"] >= 2
    assert bundle["evidence_graph"]["nodes"]
    assert bundle["evidence_graph"]["edges"]
    assert any(claim["status"] in {"supported", "partial"} for claim in bundle["claims"])


def test_classify_risk_marks_medical_topics_high():
    risk = classify_risk(
        "What are the treatment options for diabetes?",
        "Diabetes treatment should be reviewed by a clinician.",
    )

    assert risk["level"] == "high"
    assert risk["human_review_required"] is True
    assert "health" in risk["categories"]


def test_render_verification_section_mentions_human_review():
    bundle = {
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
                "claim": "Treatment options should be reviewed by a clinician.",
                "status": "unsupported",
                "confidence": 0.1,
                "sources": [],
            }
        ],
        "evidence_graph": {"nodes": [], "edges": []},
    }

    section = render_verification_section(bundle)

    assert "## Verification Review" in section
    assert "Human review required: yes" in section
    assert "Human Review Note" in section


@pytest.mark.asyncio
async def test_generate_report_appends_verification_review_and_stores_bundle(monkeypatch):
    async def fake_create_chat_completion(**kwargs):
        return """# Compare FastAPI and Flask for async Python APIs

## Overview
FastAPI is designed for async-first APIs and validates data with Pydantic.

## Key Findings
- Flask remains a compact microframework and can be combined with extensions for async support.
- FastAPI is often chosen for typed request validation.
"""

    monkeypatch.setattr(report_generation, "create_chat_completion", fake_create_chat_completion)
    monkeypatch.setattr(report_generation, "resolve_openai_base_url", lambda: None)

    cfg = Config()
    cfg.enable_verification_review = True

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

    assert "## Verification Review" in report
    assert getattr(sink, "verification_bundle", None) is not None
    assert sink.verification_bundle["summary"]["claims_total"] >= 1
