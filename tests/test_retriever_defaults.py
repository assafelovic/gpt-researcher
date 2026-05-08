from gpt_researcher.actions.retriever import (
    get_default_retriever,
    get_default_retriever_name,
)
from gpt_researcher.config.config import Config


def test_default_retriever_name_without_tavily_key_is_duckduckgo(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    assert get_default_retriever_name() == "duckduckgo"
    assert get_default_retriever().__name__ == "Duckduckgo"


def test_config_defaults_to_duckduckgo_without_tavily_key(monkeypatch):
    monkeypatch.delenv("RETRIEVER", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    cfg = Config()

    assert cfg.retrievers == ["duckduckgo"]


def test_tavily_retriever_falls_back_to_duckduckgo_without_key(monkeypatch):
    monkeypatch.setenv("RETRIEVER", "tavily")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    cfg = Config()

    assert cfg.retrievers == ["duckduckgo"]
