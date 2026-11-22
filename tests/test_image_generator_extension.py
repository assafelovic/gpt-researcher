"""A saved image's extension must follow the encoding the provider reported.

``_generate_with_gemini`` reads the encoding out of ``inline_data.mime_type`` into
``ext`` and then named every file ``.png``, so a JPEG answer was written as
``img_<hash>_0.png``: the file name, and the Content-Type ``/outputs`` serves it
with, contradicted the bytes.
"""

import sys
import types
from pathlib import Path

import pytest

from gpt_researcher.llm_provider.image.image_generator import ImageGeneratorProvider

JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 32 + b"\xff\xd9"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def _stub_genai(monkeypatch, payload: bytes, mime_type: str) -> None:
    """Answer every generate_content call with one inline image of ``mime_type``."""

    class _Models:
        @staticmethod
        def generate_content(model, contents):  # noqa: ARG004 - signature parity
            part = types.SimpleNamespace(
                inline_data=types.SimpleNamespace(data=payload, mime_type=mime_type)
            )
            content = types.SimpleNamespace(parts=[part])
            return types.SimpleNamespace(candidates=[types.SimpleNamespace(content=content)])

    class _Client:
        def __init__(self, api_key=None):
            self.models = _Models()

    genai_pkg = types.ModuleType("google.genai")
    genai_pkg.Client = _Client
    google_pkg = types.ModuleType("google")
    google_pkg.genai = genai_pkg
    monkeypatch.setitem(sys.modules, "google", google_pkg)
    monkeypatch.setitem(sys.modules, "google.genai", genai_pkg)


async def _generate(tmp_path, monkeypatch, payload: bytes, mime_type: str):
    _stub_genai(monkeypatch, payload, mime_type)
    provider = ImageGeneratorProvider(
        model_name="models/gemini-2.5-flash-image",
        api_key="test-key",
        output_dir=str(tmp_path),
    )
    return await provider.generate_image(prompt="Lithium battery thermal runway", research_id="t1")


@pytest.mark.asyncio
async def test_jpeg_answer_is_saved_as_jpg(monkeypatch, tmp_path):
    images = await _generate(tmp_path, monkeypatch, JPEG, "image/jpeg")

    assert len(images) == 1
    path = Path(images[0]["path"])
    assert path.read_bytes() == JPEG
    assert path.suffix == ".jpg"
    assert images[0]["url"].endswith(".jpg")


@pytest.mark.asyncio
async def test_png_answer_keeps_png(monkeypatch, tmp_path):
    images = await _generate(tmp_path, monkeypatch, PNG, "image/png")

    assert len(images) == 1
    path = Path(images[0]["path"])
    assert path.read_bytes() == PNG
    assert path.suffix == ".png"
    assert images[0]["url"].endswith(".png")
