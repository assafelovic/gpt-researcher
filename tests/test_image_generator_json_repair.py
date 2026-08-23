"""Image planning/analysis should recover fenced LLM JSON via json_repair."""

from types import SimpleNamespace

import pytest

from gpt_researcher.skills.image_generator import ImageGenerator


def _make_generator(max_images: int = 3) -> ImageGenerator:
    researcher = SimpleNamespace(
        cfg=SimpleNamespace(
            fast_llm_model="test",
            fast_llm_provider="openai",
            llm_kwargs={},
        ),
        add_costs=lambda *_a, **_k: None,
    )
    gen = ImageGenerator.__new__(ImageGenerator)
    gen.researcher = researcher
    gen.cfg = researcher.cfg
    gen.max_images = max_images
    gen.image_provider = None
    return gen


@pytest.mark.asyncio
async def test_plan_images_recovers_fenced_json(monkeypatch):
    gen = _make_generator()

    async def fake_chat(**kwargs):
        return (
            'Here you go:\n```json\n'
            '[{"title": "Arch", "prompt": "diagram of layers"}]\n'
            '```'
        )

    monkeypatch.setattr(
        "gpt_researcher.skills.image_generator.create_chat_completion",
        fake_chat,
    )
    concepts = await gen._plan_image_concepts("report text", "query")
    assert concepts == [{"title": "Arch", "prompt": "diagram of layers"}]


def test_parse_analysis_recovers_fenced_object():
    gen = _make_generator()
    sections = [
        {"header": "Intro", "content": "hello world", "start_line": 1},
    ]
    response = (
        'Sure.\n```json\n{"suggestions":[{"section_number":1,'
        '"image_prompt":"p","reason":"r"}]}\n```'
    )
    out = gen._parse_analysis_response(response, sections)
    assert len(out) == 1
    assert out[0]["section_header"] == "Intro"
    assert out[0]["image_prompt"] == "p"


def test_parse_analysis_skips_non_dict_suggestions():
    gen = _make_generator()
    sections = [{"header": "H", "content": "c", "start_line": 0}]
    response = '{"suggestions":[null, "x", {"section_number":1,"image_prompt":"ok"}]}'
    out = gen._parse_analysis_response(response, sections)
    assert len(out) == 1
    assert out[0]["image_prompt"] == "ok"
