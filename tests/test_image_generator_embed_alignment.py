"""Regression: a failed generation must not shift the remaining images.

``ImageGenerator.generate_images_for_report`` appends only the generations
that succeeded to ``generated_images``, but it handed the *unfiltered*
suggestion list to ``_embed_images_in_report``, which paired the two lists by
position. The moment one generation failed (an API error, a timeout, a
content filter), every later image was embedded under the previous
suggestion's section header: the report silently showed an illustration for
"Charging networks" beneath "Battery chemistry" and none at all beneath the
last section.

Each generated image already records the section it belongs to
(``image_info["section_header"]`` is set in the generation loop), so images
are now placed by that header instead of by list position.
"""

from types import SimpleNamespace

import pytest

from gpt_researcher.skills.image_generator import ImageGenerator

REPORT = (
    "# EVs\n"
    "Intro text.\n\n"
    "## Battery chemistry\n"
    "Cells and packs.\n\n"
    "## Charging networks\n"
    "Plugs and stalls.\n\n"
    "## Market share\n"
    "Sales numbers.\n"
)

# (section header, image file name) for every section the fake LLM picks.
SECTIONS = [
    ("Battery chemistry", "battery.png"),
    ("Charging networks", "charging.png"),
    ("Market share", "market.png"),
]


class _FakeProvider:
    """Image provider that fails for one section, the way an API error does."""

    def __init__(self, fail_for: set[str]):
        self.fail_for = fail_for
        self.prompts: list[str] = []

    def is_available(self) -> bool:
        return True

    async def generate_image(
        self,
        prompt,
        context="",
        research_id="",
        aspect_ratio="1:1",
        num_images=1,
        style="dark",
    ):
        self.prompts.append(prompt)
        if prompt in self.fail_for:
            raise RuntimeError("image generation unavailable")
        return [{"url": f"https://img.example/{prompt.lower().replace(' ', '-')}.png",
                 "alt_text": prompt}]


def _make_generator(fail_for: set[str]) -> ImageGenerator:
    generator = ImageGenerator.__new__(ImageGenerator)
    generator.researcher = SimpleNamespace(verbose=False, websocket=None)
    generator.cfg = SimpleNamespace(image_generation_style="dark")
    generator.max_images = len(SECTIONS)
    generator.generated_images = []
    generator.image_provider = _FakeProvider(fail_for)
    return generator


def _first_line_after(report: str, header: str) -> str | None:
    """The first non-blank line that follows ``header`` in ``report``."""
    lines = report.splitlines()
    for line in lines[lines.index(header) + 1:]:
        if line.strip():
            return line.strip()
    return None


@pytest.mark.asyncio
async def test_failed_generation_does_not_shift_remaining_images(monkeypatch):
    generator = _make_generator(fail_for={"Battery chemistry"})

    async def fake_analyze(report, query):
        return [
            {"section_header": header,
             "section_content": "",
             "image_prompt": header,
             "reason": "",
             "insert_after_line": 0}
            for header, _ in SECTIONS
        ]

    monkeypatch.setattr(generator, "analyze_report_for_images", fake_analyze)

    report, images = await generator.generate_images_for_report(REPORT, "EVs")

    assert [image["alt_text"] for image in images] == ["Charging networks", "Market share"]
    # The failed section keeps its text and gains no illustration.
    assert _first_line_after(report, "## Battery chemistry") == "Cells and packs."
    # Each generated image stays under the section it was generated for.
    assert (
        _first_line_after(report, "## Charging networks")
        == "![Charging networks](https://img.example/charging-networks.png)"
    )
    assert (
        _first_line_after(report, "## Market share")
        == "![Market share](https://img.example/market-share.png)"
    )
