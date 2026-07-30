"""Regression: filter_urls guards non-str URLs and bad excluded_domains."""

from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace


def _load_filter_urls():
    src = (
        Path(__file__).resolve().parents[1]
        / "gpt_researcher"
        / "actions"
        / "web_scraping.py"
    ).read_text()
    module = ast.parse(src)
    fn = None
    for node in module.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "filter_urls":
            fn = node
            break
    assert fn is not None
    wrapper = ast.Module(body=[fn], type_ignores=[])
    ast.fix_missing_locations(wrapper)
    ns: dict = {}
    exec(compile(wrapper, "filter_urls.py", "exec"), ns)
    return ns["filter_urls"]


filter_urls = _load_filter_urls()


def test_skips_non_string_urls():
    cfg = SimpleNamespace(excluded_domains=["bad.example"])
    out = asyncio.run(
        filter_urls(
            ["https://ok.test", None, 12, "", "https://bad.example/x"],
            cfg,
        )
    )
    assert out == ["https://ok.test"]


def test_tolerates_none_excluded_domains():
    cfg = SimpleNamespace(excluded_domains=None)
    out = asyncio.run(filter_urls(["https://ok.test"], cfg))
    assert out == ["https://ok.test"]


def test_tolerates_non_list_excluded_domains():
    cfg = SimpleNamespace(excluded_domains="not-a-list")
    out = asyncio.run(filter_urls(["https://ok.test"], cfg))
    assert out == ["https://ok.test"]
