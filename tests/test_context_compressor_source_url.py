"""ContextCompressor should preserve source links across both paths."""

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from gpt_researcher.context.compression import ContextCompressor
from gpt_researcher.prompts import PromptFamily


@pytest.mark.asyncio
@pytest.mark.parametrize("threshold", ["8000", "1"], ids=["direct", "compressed"])
async def test_context_falls_back_to_url(monkeypatch, threshold):
    monkeypatch.setenv("COMPRESSION_THRESHOLD", threshold)
    body = "Research evidence about market share."
    docs = [
        {
            "url": "https://real.example/report",
            "title": "Market share report",
            "raw_content": body,
        }
    ]
    compressor = ContextCompressor(
        documents=docs,
        embeddings=DeterministicFakeEmbedding(size=4),
        max_results=5,
        prompt_family=PromptFamily,
    )
    out = await compressor.async_get_context(body, max_results=5)
    assert "Source: https://real.example/report" in out
    assert "Title: Market share report" in out
    assert "Source: None" not in out


@pytest.mark.asyncio
@pytest.mark.parametrize("threshold", ["8000", "1"], ids=["direct", "compressed"])
async def test_context_prefers_explicit_source_key(monkeypatch, threshold):
    monkeypatch.setenv("COMPRESSION_THRESHOLD", threshold)
    body = "Research evidence about market share."
    docs = [
        {
            "url": "https://ignored.example/",
            "source": "https://canonical.example/doc",
            "title": "Canonical",
            "raw_content": body,
        }
    ]
    compressor = ContextCompressor(
        documents=docs,
        embeddings=DeterministicFakeEmbedding(size=4),
        max_results=5,
        prompt_family=PromptFamily,
    )
    out = await compressor.async_get_context(body, max_results=5)
    assert "Source: https://canonical.example/doc" in out
    assert "https://ignored.example" not in out
