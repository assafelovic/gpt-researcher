"""The deprecated EMBEDDING_PROVIDER=google_genai path must pick a served embedding model."""

import warnings

import pytest

from gpt_researcher.config.config import Config
from gpt_researcher.config.variables.default import DEFAULT_CONFIG


@pytest.fixture(autouse=True)
def clear_config_environment(monkeypatch):
    for key in DEFAULT_CONFIG:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("CONFIG_PATH", raising=False)


def test_google_genai_embedding_provider_uses_a_current_model(monkeypatch):
    # text-embedding-004 was shut down on 2026-01-14
    monkeypatch.setenv("EMBEDDING_PROVIDER", "google_genai")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)  # EMBEDDING_PROVIDER is deprecated
        config = Config()

    assert config.embedding_provider == "google_genai"
    assert config.embedding_model == "gemini-embedding-2"
