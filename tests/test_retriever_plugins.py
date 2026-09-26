"""Third-party retrievers registered through the entry-point group."""

from types import SimpleNamespace

import pytest

from gpt_researcher.actions import retriever as retriever_module
from gpt_researcher.actions.retriever import (
    RETRIEVER_ENTRY_POINT_GROUP,
    get_retriever,
    get_retrievers,
)


class AcmeSearch:
    requires_scraping = True

    def __init__(self, query, query_domains=None):
        self.query = query

    def search(self, max_results=7):
        return []


class FakeEntryPoint:
    def __init__(self, name, target=None, error=None):
        self.name = name
        self.value = f"acme_plugin:{name}"
        self.group = RETRIEVER_ENTRY_POINT_GROUP
        self._target = target
        self._error = error

    def load(self):
        if self._error:
            raise self._error
        return self._target


@pytest.fixture
def installed(monkeypatch):
    """Pretend the given entry points are installed."""

    def install(*eps):
        def fake_entry_points(*, group, name):
            return [ep for ep in eps if ep.group == group and ep.name == name]

        monkeypatch.setattr(retriever_module, "entry_points", fake_entry_points)

    return install


def test_plugin_retriever_resolves_by_name(installed):
    installed(FakeEntryPoint("acme", AcmeSearch))
    assert get_retriever("acme") is AcmeSearch


def test_unknown_name_without_plugin_is_none(installed):
    installed()
    assert get_retriever("does-not-exist") is None


def test_builtin_name_cannot_be_shadowed(installed):
    from gpt_researcher.retrievers import TavilySearch

    installed(FakeEntryPoint("tavily", AcmeSearch))
    assert get_retriever("tavily") is TavilySearch


def test_broken_plugin_is_skipped_with_a_warning(installed, caplog):
    installed(FakeEntryPoint("acme", error=ImportError("missing dependency")))
    with caplog.at_level("WARNING"):
        assert get_retriever("acme") is None
    assert "acme" in caplog.text and "missing dependency" in caplog.text


def test_get_retrievers_mixes_builtin_and_plugin(installed):
    from gpt_researcher.retrievers import Duckduckgo

    installed(FakeEntryPoint("acme", AcmeSearch))
    cfg = SimpleNamespace(retrievers=None, retriever=None)
    assert get_retrievers({"retrievers": "acme, duckduckgo"}, cfg) == [AcmeSearch, Duckduckgo]


def test_real_entry_point_lookup_returns_nothing_for_unregistered_name():
    assert retriever_module._load_plugin_retriever("gptr-test-no-such-plugin") is None


def test_config_accepts_a_plugin_retriever_name(monkeypatch):
    from gpt_researcher.config.config import Config
    from gpt_researcher.retrievers import utils as retriever_utils

    monkeypatch.setattr(retriever_utils, "get_plugin_retriever_names", lambda: ["acme"])
    assert Config().parse_retrievers("acme, tavily") == ["acme", "tavily"]
