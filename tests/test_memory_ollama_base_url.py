"""The Ollama embedding provider must default (and honour) its base URL.

``Memory("ollama", ...)`` used to read ``os.environ["OLLAMA_BASE_URL"]``
directly, so a local Ollama install -- the documented default endpoint that the
LLM provider already falls back to -- raised ``KeyError: 'OLLAMA_BASE_URL'``.
Passing ``base_url`` through ``EMBEDDING_KWARGS`` did not help either: the env
lookup ran anyway and the value was then supplied twice.
"""

import langchain_ollama
import pytest

from gpt_researcher.memory.embeddings import Memory


class _RecordingEmbeddings:
    """Stand-in for ``OllamaEmbeddings`` that records its constructor kwargs."""

    calls = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        type(self).calls.append(kwargs)


@pytest.fixture(autouse=True)
def _record_ollama_embeddings(monkeypatch):
    _RecordingEmbeddings.calls = []
    monkeypatch.setattr(langchain_ollama, "OllamaEmbeddings", _RecordingEmbeddings)


def test_ollama_base_url_defaults_to_the_local_endpoint(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    memory = Memory("ollama", "nomic-embed-text")

    assert isinstance(memory.get_embeddings(), _RecordingEmbeddings)
    assert _RecordingEmbeddings.calls == [
        {"model": "nomic-embed-text", "base_url": "http://localhost:11434"}
    ]


def test_ollama_base_url_from_environment_is_used(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.internal:11434")

    Memory("ollama", "nomic-embed-text")

    assert _RecordingEmbeddings.calls[0]["base_url"] == "http://ollama.internal:11434"


def test_explicit_ollama_base_url_kwarg_wins(monkeypatch):
    # EMBEDDING_KWARGS={"base_url": ...} is the documented escape hatch; it must
    # neither be ignored nor passed twice.
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.internal:11434")

    Memory("ollama", "nomic-embed-text", base_url="http://127.0.0.1:9999")

    assert _RecordingEmbeddings.calls[0]["base_url"] == "http://127.0.0.1:9999"
