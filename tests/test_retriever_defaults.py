from types import SimpleNamespace

from gpt_researcher.actions.retriever import (
    get_default_retriever,
    get_default_retriever_name,
    get_retriever,
    get_retrievers,
    normalize_retriever_name,
    normalize_retriever_names,
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


def test_normalize_retriever_name_empty_falls_back(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    assert normalize_retriever_name("") == "duckduckgo"
    assert normalize_retriever_name(None) == "duckduckgo"


def test_normalize_retriever_name_tavily_without_key_falls_back(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    assert normalize_retriever_name("tavily") == "duckduckgo"


def test_normalize_retriever_name_passthrough():
    assert normalize_retriever_name("google") == "google"
    assert normalize_retriever_name("  DuckDuckGo  ") == "duckduckgo"


def test_normalize_retriever_names_deduplicates():
    result = normalize_retriever_names(["duckduckgo", "duckduckgo", "google"])
    assert result == ["duckduckgo", "google"]


def test_normalize_retriever_names_skips_empty():
    result = normalize_retriever_names(["duckduckgo", "", "google"])
    assert result == ["duckduckgo", "google"]


def test_get_retriever_duckduckgo():
    from gpt_researcher.retrievers import Duckduckgo
    assert get_retriever("duckduckgo") is Duckduckgo


def test_get_retriever_google():
    from gpt_researcher.retrievers import GoogleSearch
    assert get_retriever("google") is GoogleSearch


def test_get_retriever_bing():
    from gpt_researcher.retrievers import BingSearch
    assert get_retriever("bing") is BingSearch


def test_get_retriever_tavily(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    from gpt_researcher.retrievers import TavilySearch
    assert get_retriever("tavily") is TavilySearch


def test_get_retriever_unknown_returns_default(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    from gpt_researcher.retrievers import Duckduckgo
    assert get_retriever("nonexistent") is None


def test_get_retriever_arxiv():
    from gpt_researcher.retrievers import ArxivSearch
    assert get_retriever("arxiv") is ArxivSearch


def test_get_retrievers_from_headers():
    from gpt_researcher.retrievers import Duckduckgo
    cfg = SimpleNamespace(retrievers=["duckduckgo"])
    result = get_retrievers({"retrievers": "duckduckgo"}, cfg)
    assert result == [Duckduckgo]


def test_get_retrievers_from_cfg():
    from gpt_researcher.retrievers import Duckduckgo
    cfg = SimpleNamespace(retrievers="duckduckgo", retriever=None)
    result = get_retrievers({}, cfg)
    assert result == [Duckduckgo]


def test_get_retrievers_fallback_to_default(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    from gpt_researcher.retrievers import Duckduckgo
    cfg = SimpleNamespace(retrievers=[], retriever=None)
    result = get_retrievers({}, cfg)
    assert result == [Duckduckgo]


def test_get_default_retriever_with_tavily_key(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    from gpt_researcher.retrievers import TavilySearch
    assert get_default_retriever() is TavilySearch
