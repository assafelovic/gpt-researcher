"""Tests for the VisionAnalyzer skill.

Covers opt-in gating, caption injection into scraped sources, per-source and
global image caps, URL deduplication, failure isolation between images, the
SSRF guard, the OpenAI-compatible VLM payload parsing, and config handling.
"""

import types

import pytest

from gpt_researcher.config.config import Config
from gpt_researcher.skills.vision_analyzer import VisionAnalyzer, _extract_chat_content


def _make_researcher(cfg=None):
    cfg = cfg or Config()
    return types.SimpleNamespace(cfg=cfg, verbose=False, websocket=None)


def _make_analyzer(monkeypatch, **env):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    analyzer = VisionAnalyzer(_make_researcher())
    assert analyzer.is_enabled()
    return analyzer


def _scraped_data():
    return [
        {
            "url": "https://example.com/a",
            "title": "Paper A",
            "raw_content": "Body A",
            "image_urls": [
                {"url": "https://cdn.example.com/fig1.png", "score": 3},
                {"url": "https://cdn.example.com/fig2.jpg", "score": 1},
            ],
        },
        {
            "url": "https://example.com/b",
            "title": "Paper B",
            "raw_content": "Body B",
            "image_urls": [{"url": "https://cdn.example.com/fig1.png", "score": 2}],
        },
    ]


@pytest.mark.asyncio
async def test_disabled_by_default_returns_sources_untouched():
    analyzer = VisionAnalyzer(_make_researcher())
    assert analyzer.is_enabled() is False

    sources = _scraped_data()
    result = await analyzer.analyze(sources, "query")
    assert result is sources
    assert "image_captions" not in sources[0]
    assert sources[0]["raw_content"] == "Body A"


def test_config_lowercases_vision_keys(monkeypatch):
    monkeypatch.setenv("VISION_ENABLED", "true")
    monkeypatch.setenv("VISION_MAX_IMAGES", "7")
    cfg = Config()
    assert cfg.vision_enabled is True
    assert cfg.vision_max_images == 7
    assert not hasattr(cfg, "VISION_ENABLED")


@pytest.mark.asyncio
async def test_appends_caption_block_and_metadata(monkeypatch):
    analyzer = _make_analyzer(
        monkeypatch,
        VISION_ENABLED="true",
        VISION_MAX_IMAGES="4",
        VISION_MAX_IMAGES_PER_SOURCE="2",
    )
    monkeypatch.setattr(
        "gpt_researcher.skills.vision_analyzer.validate_url", lambda url: url
    )
    downloaded = []

    async def fake_download(url):
        downloaded.append(url)
        return b"fake-png-bytes", "image/png"

    async def fake_vlm(**kwargs):
        return {
            "url": kwargs["url"],
            "title": kwargs["title"],
            "caption": "A bar chart of mortality by arm",
            "text": "Placebo 12% / Treatment 8%",
            "relevant": True,
        }

    analyzer.image_downloader = fake_download
    analyzer.vlm_caller = fake_vlm

    sources = _scraped_data()
    result = await analyzer.analyze(sources, "beta blockers in heart failure")

    # fig1.png appears in both sources but is analyzed only once; fig2.jpg is
    # the second candidate because the per-source cap is two.
    assert downloaded == [
        "https://cdn.example.com/fig1.png",
        "https://cdn.example.com/fig2.jpg",
    ]
    assert len(result[0]["image_captions"]) == 2
    assert result[0]["image_captions"][0]["caption"].startswith("A bar chart")
    assert "[Visual evidence from images in this source]" in result[0]["raw_content"]
    assert "Body A" in result[0]["raw_content"]
    # Source B only carried the deduplicated fig1 image, so it stays unchanged.
    assert "image_captions" not in result[1]
    assert result[1]["raw_content"] == "Body B"


@pytest.mark.asyncio
async def test_honours_global_cap(monkeypatch):
    analyzer = _make_analyzer(
        monkeypatch,
        VISION_ENABLED="true",
        VISION_MAX_IMAGES="1",
        VISION_MAX_IMAGES_PER_SOURCE="2",
    )
    monkeypatch.setattr(
        "gpt_researcher.skills.vision_analyzer.validate_url", lambda url: url
    )
    calls = []

    async def fake_download(url):
        calls.append(url)
        return b"img", "image/png"

    async def fake_vlm(**kwargs):
        return {"url": kwargs["url"], "caption": "c", "text": "", "relevant": True}

    analyzer.image_downloader = fake_download
    analyzer.vlm_caller = fake_vlm

    await analyzer.analyze(_scraped_data(), "q")
    assert calls == ["https://cdn.example.com/fig1.png"]


@pytest.mark.asyncio
async def test_one_failed_image_does_not_break_the_others(monkeypatch):
    analyzer = _make_analyzer(
        monkeypatch,
        VISION_ENABLED="true",
        VISION_MAX_IMAGES="4",
        VISION_MAX_IMAGES_PER_SOURCE="2",
    )
    monkeypatch.setattr(
        "gpt_researcher.skills.vision_analyzer.validate_url", lambda url: url
    )

    async def fake_download(url):
        return b"img", "image/png"

    async def fake_vlm(**kwargs):
        if kwargs["url"].endswith("fig2.jpg"):
            raise RuntimeError("endpoint exploded")
        return {"url": kwargs["url"], "caption": "ok caption", "text": "", "relevant": True}

    analyzer.image_downloader = fake_download
    analyzer.vlm_caller = fake_vlm

    sources = _scraped_data()
    result = await analyzer.analyze(sources, "q")
    captions = result[0]["image_captions"]
    assert [c["url"] for c in captions] == ["https://cdn.example.com/fig1.png"]
    assert result[0]["raw_content"].count("[Visual evidence") == 1


@pytest.mark.asyncio
async def test_no_images_is_a_noop(monkeypatch):
    analyzer = _make_analyzer(monkeypatch, VISION_ENABLED="true")
    sources = [{"url": "u", "title": "t", "raw_content": "text", "image_urls": []}]
    result = await analyzer.analyze(sources, "q")
    assert result is sources
    assert "image_captions" not in sources[0]


@pytest.mark.asyncio
async def test_unsafe_image_url_is_skipped(monkeypatch):
    analyzer = _make_analyzer(monkeypatch, VISION_ENABLED="true")
    sources = [
        {
            "url": "https://example.com/a",
            "title": "Paper A",
            "raw_content": "Body A",
            "image_urls": [{"url": "file:///etc/passwd", "score": 1}],
        }
    ]
    result = await analyzer.analyze(sources, "q")
    assert result is sources
    assert "image_captions" not in sources[0]


def test_parse_description_recovers_fenced_json():
    analyzer = VisionAnalyzer(_make_researcher())
    parsed = analyzer._parse_description(
        'Sure:\n```json\n{"caption": "a chart", "text": "12%", "relevant": true}\n```',
        "https://cdn.example.com/x.png",
        "Paper A",
    )
    assert parsed["caption"] == "a chart"
    assert parsed["text"] == "12%"
    assert parsed["relevant"] is True


def test_extract_chat_content_accepts_string_and_block_list():
    assert _extract_chat_content({"choices": [{"message": {"content": "hello"}}]}) == "hello"
    blocks = {
        "choices": [
            {
                "message": {
                    "content": [
                        {"type": "text", "text": "a"},
                        {"type": "text", "text": "b"},
                    ]
                }
            }
        ]
    }
    assert _extract_chat_content(blocks) == "ab"
