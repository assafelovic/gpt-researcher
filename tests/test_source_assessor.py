from types import SimpleNamespace

import pytest

from gpt_researcher.skills import source_assessor as source_assessor_module
from gpt_researcher.skills.source_assessor import SourceAssessor


class FakeResearcher:
    def __init__(self, *, max_content_chars=12000):
        self.cfg = SimpleNamespace(
            fast_llm_model="fast-model",
            fast_llm_provider="fast-provider",
            fast_token_limit=1000,
            llm_kwargs={"response_format": "json"},
        )
        self.source_assessment_prompt = "Accept independent sources only."
        self.source_assessment_threshold = 0.25
        self.source_assessment_max_content_chars = max_content_chars
        self.source_assessment_max_concurrency = 2
        self.source_assessments = []
        self.costs = []

    def add_costs(self, cost):
        self.costs.append(cost)

    def add_source_assessments(self, assessments):
        self.source_assessments.extend(assessments)


@pytest.mark.asyncio
async def test_source_assessor_accepts_source(monkeypatch):
    async def fake_create_chat_completion(**kwargs):
        return '{"score": 0.1, "reason": "Independent data.", "matched_policy": "independent"}'

    monkeypatch.setattr(source_assessor_module, "create_chat_completion", fake_create_chat_completion)
    researcher = FakeResearcher()

    accepted, rejected = await SourceAssessor(researcher).assess_sources([
        {
            "url": "https://example.com/accepted",
            "title": "Accepted",
            "raw_content": "Independent observed outcome data.",
        }
    ])

    assert [source["url"] for source in accepted] == ["https://example.com/accepted"]
    assert rejected == []
    assert researcher.source_assessments == [
        {
            "url": "https://example.com/accepted",
            "title": "Accepted",
            "accepted": True,
            "score": 0.1,
            "reason": "Independent data.",
            "matched_policy": "independent",
        }
    ]


@pytest.mark.asyncio
async def test_source_assessor_rejects_source(monkeypatch):
    async def fake_create_chat_completion(**kwargs):
        return '{"score": 0.9, "reason": "Derived source.", "matched_policy": "derivative"}'

    monkeypatch.setattr(source_assessor_module, "create_chat_completion", fake_create_chat_completion)
    researcher = FakeResearcher()

    accepted, rejected = await SourceAssessor(researcher).assess_sources([
        {
            "url": "https://example.com/rejected",
            "title": "Rejected",
            "raw_content": "This page repeats the original source.",
        }
    ])

    assert accepted == []
    assert rejected == [
        {
            "url": "https://example.com/rejected",
            "title": "Rejected",
            "accepted": False,
            "score": 0.9,
            "reason": "Derived source.",
            "matched_policy": "derivative",
        }
    ]


@pytest.mark.asyncio
async def test_source_assessor_ignores_model_accepted_flag(monkeypatch):
    async def fake_create_chat_completion(**kwargs):
        return '{"accepted": true, "score": 0.6, "reason": "Partial match.", "matched_policy": "clause"}'

    monkeypatch.setattr(source_assessor_module, "create_chat_completion", fake_create_chat_completion)
    researcher = FakeResearcher()

    accepted, rejected = await SourceAssessor(researcher).assess_sources([
        {
            "url": "https://example.com/mid",
            "title": "Mid",
            "raw_content": "Content",
        }
    ])

    assert accepted == []
    assert rejected[0]["accepted"] is False
    assert rejected[0]["score"] == 0.6


@pytest.mark.asyncio
async def test_source_assessor_accepts_score_only_json(monkeypatch):
    async def fake_create_chat_completion(**kwargs):
        return '{"score": 0.1, "reason": "No violation.", "matched_policy": "independent"}'

    monkeypatch.setattr(source_assessor_module, "create_chat_completion", fake_create_chat_completion)
    researcher = FakeResearcher()

    accepted, rejected = await SourceAssessor(researcher).assess_sources([
        {
            "url": "https://example.com/score-only",
            "title": "Score only",
            "raw_content": "Content",
        }
    ])

    assert [source["url"] for source in accepted] == ["https://example.com/score-only"]
    assert rejected == []


@pytest.mark.asyncio
async def test_source_assessor_rejects_out_of_range_score(monkeypatch):
    async def fake_create_chat_completion(**kwargs):
        return '{"score": 80, "reason": "Looks independent.", "matched_policy": "independent"}'

    monkeypatch.setattr(source_assessor_module, "create_chat_completion", fake_create_chat_completion)
    researcher = FakeResearcher()

    accepted, rejected = await SourceAssessor(researcher).assess_sources([
        {
            "url": "https://example.com/percent",
            "title": "Percent",
            "raw_content": "Content",
        }
    ])

    assert accepted == []
    assert rejected[0]["accepted"] is False
    assert rejected[0]["score"] == 0.0
    assert "0.0, 1.0" in rejected[0]["reason"]


@pytest.mark.asyncio
async def test_source_assessor_prompt_describes_violation_scale(monkeypatch):
    captured_messages = []

    async def fake_create_chat_completion(**kwargs):
        captured_messages.extend(kwargs["messages"])
        return '{"score": 0.1, "reason": "ok", "matched_policy": "all"}'

    monkeypatch.setattr(source_assessor_module, "create_chat_completion", fake_create_chat_completion)
    researcher = FakeResearcher()

    await SourceAssessor(researcher).assess_sources([
        {
            "url": "https://example.com/prompt",
            "title": "Prompt",
            "raw_content": "Content",
        }
    ])

    system_content = captured_messages[0]["content"]
    user_content = captured_messages[1]["content"]
    combined = f"{system_content}\n{user_content}"
    assert "violat" in combined.lower()
    assert "0.0" in combined
    assert "1.0" in combined
    assert "admit if score" not in combined.lower()
    assert '{"score": 0.0, "reason": "", "matched_policy": ""}' in user_content


@pytest.mark.asyncio
async def test_source_assessor_full_content_when_max_chars_is_negative_one(monkeypatch):
    captured_prompt = ""

    async def fake_create_chat_completion(**kwargs):
        nonlocal captured_prompt
        captured_prompt = kwargs["messages"][1]["content"]
        return '{"score": 0.1, "reason": "ok", "matched_policy": "all"}'

    monkeypatch.setattr(source_assessor_module, "create_chat_completion", fake_create_chat_completion)
    researcher = FakeResearcher(max_content_chars=-1)
    raw_content = "A" * 13000 + "TAIL"

    await SourceAssessor(researcher).assess_sources([
        {
            "url": "https://example.com/full",
            "title": "Full",
            "raw_content": raw_content,
        }
    ])

    assert raw_content in captured_prompt
    assert "TAIL" in captured_prompt


@pytest.mark.asyncio
async def test_source_assessor_rejects_malformed_output(monkeypatch):
    async def fake_create_chat_completion(**kwargs):
        return "not-json"

    monkeypatch.setattr(source_assessor_module, "create_chat_completion", fake_create_chat_completion)
    researcher = FakeResearcher()

    accepted, rejected = await SourceAssessor(researcher).assess_sources([
        {
            "url": "https://example.com/bad-json",
            "title": "Bad JSON",
            "raw_content": "Content",
        }
    ])

    assert accepted == []
    assert rejected[0]["accepted"] is False
    assert rejected[0]["score"] == 0.0
    assert "not a JSON object" in rejected[0]["reason"]


@pytest.mark.asyncio
async def test_source_assessor_rejects_llm_failure(monkeypatch):
    async def fake_create_chat_completion(**kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr(source_assessor_module, "create_chat_completion", fake_create_chat_completion)
    researcher = FakeResearcher()

    accepted, rejected = await SourceAssessor(researcher).assess_sources([
        {
            "url": "https://example.com/failure",
            "title": "Failure",
            "raw_content": "Content",
        }
    ])

    assert accepted == []
    assert rejected[0]["accepted"] is False
    assert rejected[0]["score"] == 0.0
    assert "provider down" in rejected[0]["reason"]
