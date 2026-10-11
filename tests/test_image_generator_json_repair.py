"""Image planning/analysis should recover fenced LLM JSON via json_repair."""

from types import SimpleNamespace

import pytest

from gpt_researcher.config.config import Config
from gpt_researcher.llm_provider.image import ModelsLabImageGeneratorProvider
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


def _config_from_env(monkeypatch):
    """A real Config plus a researcher namespace, so _init_provider runs for real."""
    cfg = Config()
    return SimpleNamespace(cfg=cfg, verbose=False, websocket=None, headers={})


def test_config_lowercases_image_generation_keys(monkeypatch):
    """Config._set_attributes() stores keys as key.lower().

    This is why ImageGenerator must read 'image_generation_enabled' rather
    than 'IMAGE_GENERATION_ENABLED' -- the uppercase name never resolves.
    """
    monkeypatch.setenv("IMAGE_GENERATION_ENABLED", "true")
    cfg = Config()
    assert getattr(cfg, "image_generation_enabled", None) is True
    assert not hasattr(cfg, "IMAGE_GENERATION_ENABLED")


def test_init_provider_builds_provider_when_enabled(monkeypatch):
    monkeypatch.setenv("IMAGE_GENERATION_ENABLED", "true")
    monkeypatch.setenv("IMAGE_GENERATION_PROVIDER", "modelslab")
    monkeypatch.setenv("IMAGE_GENERATION_MODEL", "flux")
    monkeypatch.setenv("IMAGE_GENERATION_MAX_IMAGES", "9")
    monkeypatch.setenv("MODELSLAB_API_KEY", "test-key")

    gen = ImageGenerator(_config_from_env(monkeypatch))

    assert isinstance(gen.image_provider, ModelsLabImageGeneratorProvider)
    assert gen.is_enabled() is True
    assert gen.max_images == 9


def test_init_provider_stays_off_when_disabled(monkeypatch):
    """The fix must not force-enable image generation."""
    monkeypatch.setenv("IMAGE_GENERATION_ENABLED", "false")
    monkeypatch.setenv("IMAGE_GENERATION_PROVIDER", "modelslab")
    monkeypatch.setenv("MODELSLAB_API_KEY", "test-key")

    gen = ImageGenerator(_config_from_env(monkeypatch))

    assert gen.image_provider is None
    assert gen.is_enabled() is False


def test_parse_analysis_skips_non_dict_suggestions():
    gen = _make_generator()
    sections = [{"header": "H", "content": "c", "start_line": 0}]
    response = '{"suggestions":[null, "x", {"section_number":1,"image_prompt":"ok"}]}'
    out = gen._parse_analysis_response(response, sections)
    assert len(out) == 1
    assert out[0]["image_prompt"] == "ok"
