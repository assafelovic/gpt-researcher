import pytest
from backend.server.app import ResearchRequest

def test_research_request_valid_minimal():
    """Test creating ResearchRequest with minimal required fields."""
    req = ResearchRequest(
        task="Test Task",
        report_type="research_report",
        report_source="web",
        tone="Objective"
    )
    assert req.task == "Test Task"
    assert req.report_type == "research_report"
    assert req.report_source == "web"
    assert req.tone == "Objective"
    assert req.headers is None
    assert req.user_id is None
    assert req.language is None
    assert req.project_id is None
    assert req.research_id is None

def test_research_request_all_fields():
    """Test creating ResearchRequest with all fields populated."""
    req = ResearchRequest(
        task="Test Task",
        report_type="detailed_report",
        report_source="web",
        tone="Formal",
        headers={"User-Agent": "Test"},
        user_id=123,
        language="zh-CN",
        project_id="proj_001",
        research_id="custom_id_1"
    )
    assert req.task == "Test Task"
    assert req.headers == {"User-Agent": "Test"}
    assert req.user_id == 123
    assert req.language == "zh-CN"
    assert req.project_id == "proj_001"
    assert req.research_id == "custom_id_1"

def test_research_request_optional_fields_defaults():
    """Ensure optional fields default to None."""
    req = ResearchRequest(
        task="Test Task",
        report_type="research_report",
        report_source="web",
        tone="Objective"
    )
    assert req.headers is None
    assert req.user_id is None
    assert req.language is None
    assert req.project_id is None
    assert req.research_id is None
