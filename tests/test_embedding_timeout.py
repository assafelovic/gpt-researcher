"""EMBEDDING_TIMEOUT bounds embedding-based compression so a stalled provider cannot hang a run."""

import time
from types import SimpleNamespace

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from gpt_researcher.context.compression import ContextCompressor, WrittenContentCompressor, embedding_timeout
from gpt_researcher.context.select import select_context

ANSWER = "Solid-state batteries cost about $400 per kWh in 2026, roughly three times lithium-ion cells. "


class SlowEmbedding(DeterministicFakeEmbedding):
    delay: float = 1.0

    def embed_documents(self, texts):
        time.sleep(self.delay)
        return super().embed_documents(texts)


def _pages():
    return [{"url": "answer", "title": "answer", "raw_content": ANSWER * 20}]


@pytest.fixture(autouse=True)
def _compress_everything(monkeypatch):
    monkeypatch.setenv("COMPRESSION_THRESHOLD", "1")


@pytest.mark.asyncio
async def test_stalled_embeddings_raise_a_clear_timeout(monkeypatch):
    monkeypatch.setenv("EMBEDDING_TIMEOUT", "0.05")
    compressor = ContextCompressor(documents=_pages(), embeddings=SlowEmbedding(size=4), max_results=1)
    with pytest.raises(TimeoutError, match="EMBEDDING_TIMEOUT"):
        await compressor.async_get_context("battery cost", max_results=1)


@pytest.mark.asyncio
async def test_written_content_compressor_is_bounded_too(monkeypatch):
    monkeypatch.setenv("EMBEDDING_TIMEOUT", "0.05")
    sections = [{"section_title": "Battery costs", "written_content": ANSWER * 3}]
    compressor = WrittenContentCompressor(documents=sections, embeddings=SlowEmbedding(size=4), similarity_threshold=0.0)
    with pytest.raises(TimeoutError, match="EMBEDDING_TIMEOUT"):
        await compressor.async_get_context("battery cost")


@pytest.mark.asyncio
async def test_select_context_falls_back_to_keywords_on_timeout(monkeypatch):
    monkeypatch.setenv("EMBEDDING_TIMEOUT", "0.05")
    cfg = SimpleNamespace(context_filter="embeddings", similarity_threshold=0.0)
    started = time.monotonic()
    context = await select_context("battery cost", _pages(), cfg, embeddings=lambda: SlowEmbedding(size=4))
    assert time.monotonic() - started < SlowEmbedding.model_fields["delay"].default
    assert "$400 per kWh" in context


@pytest.mark.asyncio
async def test_zero_disables_the_timeout(monkeypatch):
    monkeypatch.setenv("EMBEDDING_TIMEOUT", "0")
    compressor = ContextCompressor(
        documents=_pages(), embeddings=SlowEmbedding(size=4, delay=0.1), max_results=1, similarity_threshold=0.0,
    )
    assert "Source: answer" in await compressor.async_get_context("battery cost", max_results=1)


def test_default_timeout(monkeypatch):
    monkeypatch.delenv("EMBEDDING_TIMEOUT", raising=False)
    assert embedding_timeout() == 120.0


@pytest.mark.parametrize("value", ["-1", "nan", "inf", "soon"])
def test_invalid_timeout_is_rejected(monkeypatch, value):
    monkeypatch.setenv("EMBEDDING_TIMEOUT", value)
    with pytest.raises(ValueError, match="EMBEDDING_TIMEOUT"):
        embedding_timeout()
