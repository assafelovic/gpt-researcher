"""Regression: ContextCompressor fast path must map url -> metadata.source."""

import os
from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document

from gpt_researcher.context.compression import ContextCompressor
from gpt_researcher.prompts import PromptFamily


@pytest.mark.asyncio
async def test_fast_path_maps_url_to_source_metadata(monkeypatch):
    monkeypatch.setenv("COMPRESSION_THRESHOLD", "8000")
    docs = [
        {
            "url": "https://real.example/report",
            "title": "Market share report",
            "raw_content": "snippet content under threshold",
        }
    ]
    compressor = ContextCompressor(
        documents=docs,
        embeddings=MagicMock(),
        max_results=5,
        prompt_family=PromptFamily,
    )
    out = await compressor.async_get_context("market share", max_results=5)
    assert "Source: https://real.example/report" in out
    assert "Title: Market share report" in out
    assert "Source: None" not in out


@pytest.mark.asyncio
async def test_fast_path_prefers_explicit_source_key(monkeypatch):
    monkeypatch.setenv("COMPRESSION_THRESHOLD", "8000")
    docs = [
        {
            "url": "https://ignored.example/",
            "source": "https://canonical.example/doc",
            "title": "Canonical",
            "raw_content": "short body",
        }
    ]
    compressor = ContextCompressor(
        documents=docs,
        embeddings=MagicMock(),
        max_results=5,
        prompt_family=PromptFamily,
    )
    out = await compressor.async_get_context("q", max_results=5)
    assert "Source: https://canonical.example/doc" in out
    assert "https://ignored.example" not in out
