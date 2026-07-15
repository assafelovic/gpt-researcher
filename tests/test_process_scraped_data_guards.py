"""process_scraped_data must not KeyError on partial scrape dicts.

Strict item['status'] / item['content'] / item['url'] access aborted
post-processing the rest of the batch when one entry was partial.
"""
from __future__ import annotations

import asyncio
import importlib.util
import pathlib
import sys
import types
from unittest.mock import MagicMock


def _mod(name: str):
    m = types.ModuleType(name)
    sys.modules[name] = m
    return m


sys.modules.setdefault(
    "colorama",
    types.SimpleNamespace(
        Fore=types.SimpleNamespace(RED=""),
        Style=types.SimpleNamespace(RESET_ALL=""),
    ),
)
_mod("gpt_researcher")
_mod("gpt_researcher.utils")
_workers = _mod("gpt_researcher.utils.workers")
_workers.WorkerPool = object
_logger = _mod("gpt_researcher.utils.logger")
_logger.get_formatted_logger = lambda: MagicMock()
_scraper = _mod("gpt_researcher.scraper")
_scraper.Scraper = object
_mod("gpt_researcher.config")
_cfgm = _mod("gpt_researcher.config.config")
_cfgm.Config = object
_mod("gpt_researcher.actions")

web_path = (
    pathlib.Path(__file__).resolve().parent.parent
    / "gpt_researcher"
    / "actions"
    / "web_scraping.py"
)
spec = importlib.util.spec_from_file_location(
    "gpt_researcher.actions.web_scraping",
    web_path,
)
ws = importlib.util.module_from_spec(spec)
sys.modules["gpt_researcher.actions.web_scraping"] = ws
ws.__package__ = "gpt_researcher.actions"
spec.loader.exec_module(ws)


def test_process_scraped_data_success_and_partial():
    data = [
        {"status": "success", "url": "https://a.example", "content": "<p>hi</p>"},
        {"status": "error", "url": "https://b.example", "error": "x"},
        "not-a-dict",
        {"status": "success"},  # missing url/content
    ]

    out = asyncio.run(ws.process_scraped_data(data, config=None))
    assert out[0]["status"] == "success"
    assert out[0]["url"] == "https://a.example"
    assert out[0]["content"] == "<p>hi</p>"
    assert out[1]["status"] == "error"
    assert out[2] == {"url": "", "content": "", "status": "success"}


def test_process_scraped_data_missing_status_not_success():
    data = [{"url": "https://c.example", "content": "x"}]
    out = asyncio.run(ws.process_scraped_data(data, config=None))
    assert out == data
