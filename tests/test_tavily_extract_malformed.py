"""TavilyExtract must tolerate partial/malformed extract API payloads.

Without the fix, missing ``failed_results`` / ``results`` / ``raw_content``
keys KeyError into the broad except and return empty — and when
``session is None`` (constructor default) AttributeError on session.get
discards extract content that *is* present.
"""
from __future__ import annotations

import os
import sys
import types
from unittest.mock import patch


_fake_tavily = types.ModuleType("tavily")


class _FakeClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self._response = None

    def extract(self, urls=None):
        return self._response


_fake_tavily.TavilyClient = _FakeClient

import importlib.util
import pathlib

_path = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "scraper"
    / "tavily_extract"
    / "tavily_extract.py"
)
_spec = importlib.util.spec_from_file_location("_tavily_extract_ut", _path)
_mod = importlib.util.module_from_spec(_spec)
# Provide package context for relative imports inside the module
_mod.__package__ = "gpt_researcher.scraper.tavily_extract"
sys.modules["_tavily_extract_ut"] = _mod
_spec.loader.exec_module(_mod)
TavilyExtract = _mod.TavilyExtract


def _build(response, session=None):
    os.environ["TAVILY_API_KEY"] = "test-key"
    # TavilyExtract imports tavily lazily, in __init__.
    with patch.dict(sys.modules, {"tavily": _fake_tavily}):
        inst = TavilyExtract("https://example.com/a", session=session)
    inst.tavily_client._response = response
    return inst


def test_successful_payload_returns_content_without_session():
    inst = _build(
        {
            "failed_results": [],
            "results": [{"raw_content": "hello world"}],
        },
        session=None,
    )
    content, images, title = inst.scrape()
    assert content == "hello world"
    assert images == []
    assert title == ""


def test_missing_failed_results_key_still_returns_content():
    inst = _build({"results": [{"raw_content": "body"}]}, session=None)
    content, _, _ = inst.scrape()
    assert content == "body"


def test_null_results_returns_empty():
    inst = _build({"failed_results": [], "results": None})
    assert inst.scrape() == ("", [], "")


def test_empty_results_returns_empty():
    inst = _build({"failed_results": [], "results": []})
    assert inst.scrape() == ("", [], "")


def test_failed_results_present_returns_empty():
    inst = _build(
        {
            "failed_results": [{"url": "https://example.com/a"}],
            "results": [{"raw_content": "should be ignored"}],
        }
    )
    assert inst.scrape() == ("", [], "")


def test_missing_raw_content_key_returns_empty():
    inst = _build(
        {"failed_results": [], "results": [{"url": "https://example.com/a"}]}
    )
    assert inst.scrape() == ("", [], "")
