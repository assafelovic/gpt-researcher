"""Tests that stub sys.modules must put it back the way they found it.

Several tests load their module under test against hand-built stand-ins for
``gpt_researcher``, ``multi_agents``, ``bs4``, ``requests``, ``arxiv``, ... in
``sys.modules``. Left behind, a stub replaces the real package for every test
that runs afterwards, so the suite passes or fails depending on test order.

Each case below runs one of those stubbing sites with the real packages already
imported, and asserts that nothing in ``sys.modules`` was replaced or removed,
that no stub module was left behind, and that no real module was patched.
"""
import importlib
import runpy
import sys
import unittest
from pathlib import Path

import pytest

# Import the real packages first, so a leaked stub shows up as a replacement.
import arxiv  # noqa: F401
import bs4  # noqa: F401
import langchain_community.document_loaders  # noqa: F401
import langchain_community.vectorstores  # noqa: F401
import langchain_core.documents  # noqa: F401
import langchain_text_splitters  # noqa: F401
import multi_agents
import requests
import gpt_researcher.config.config
import gpt_researcher.document.document  # noqa: F401
import gpt_researcher.scraper.utils  # noqa: F401
import gpt_researcher.utils.url_security  # noqa: F401

TESTS = Path(__file__).resolve().parent
# Attributes that earlier versions of these tests overwrote on the real modules.
REAL_ATTRS = [
    (gpt_researcher.config.config, "Config"),
    (requests, "Session"),
    (multi_agents, "__path__"),
]


def _call(module, name, *args):
    return lambda: getattr(importlib.import_module(f"tests.{module}"), name)(*args)


def _run_file(module):
    return lambda: runpy.run_path(str(TESTS / f"{module}.py"))


def _run_testcase(module, cls):
    def run():
        case = getattr(importlib.import_module(f"tests.{module}"), cls)
        result = unittest.TestResult()
        unittest.defaultTestLoader.loadTestsFromTestCase(case).run(result)
        assert result.wasSuccessful(), result.failures + result.errors

    return run


SITES = {
    "bs_session_none": _call("test_bs_session_none", "_load"),
    "document_loader": _call("test_document_loader_metadata_source", "_load"),
    "duckduckgo": _call("test_duckduckgo_normalize", "_load_duckduckgo_module"),
    "groundroute": _call("test_groundroute_malformed_results", "_load"),
    "openalex": _call("test_openalex_malformed_results", "_load"),
    "report_generation": _call("test_report_generation_available_images", "_load_module"),
    "scraper_images": _call("test_scraper_images_class_guard", "_load"),
    "scraper_run": _call("test_scraper_run_guards", "_load_scraper_module"),
    "searx": _call("test_searx_malformed_results", "_load"),
    "vector_store": _call("test_vector_store_doc_guards", "_load"),
    "websocket_manager": _call("test_websocket_manager", "_load_websocket_manager_module"),
    "tavily_extract": _call("test_tavily_extract_malformed", "_build", {}),
    "arxiv_scraper": _call("test_arxiv_scraper_empty", "test_scrape_returns_doc_when_present"),
    "arxiv_retriever": _run_file("test_arxiv_null_fields"),
    "azure_document_loader": _run_file("test_azure_document_loader"),
    "publisher": _run_file("test_publisher_layout_guards"),
    "reviewer": _run_file("test_reviewer_guidelines_guard"),
    "web_base_loader_docs": _run_testcase("test_web_base_loader_docs_guard", "WebBaseLoaderDocsGuard"),
    "web_base_loader_enrichment": _run_testcase(
        "test_web_base_loader_enrichment_guard", "WebBaseLoaderEnrichmentGuard"
    ),
}


@pytest.mark.parametrize("site", SITES)
def test_stubs_do_not_outlive_their_site(site):
    before = dict(sys.modules)
    attrs = [getattr(mod, name) for mod, name in REAL_ATTRS]

    SITES[site]()

    after = sys.modules
    replaced = [k for k, mod in before.items() if after.get(k) is not mod]
    stubs = [k for k in after.keys() - before.keys() if getattr(after[k], "__spec__", 0) is None]
    assert replaced == [] and stubs == []
    assert all(getattr(mod, name) is attr for (mod, name), attr in zip(REAL_ATTRS, attrs))
