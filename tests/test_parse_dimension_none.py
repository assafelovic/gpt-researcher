"""parse_dimension must tolerate None/non-str width/height attrs."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load():
    path = Path(__file__).resolve().parents[1] / "gpt_researcher" / "scraper" / "utils.py"
    spec = importlib.util.spec_from_file_location("scraper_utils_ut", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_parse_dimension_none():
    u = _load()
    assert u.parse_dimension(None) is None


def test_parse_dimension_px_and_int():
    u = _load()
    assert u.parse_dimension("100px") == 100
    assert u.parse_dimension(80) == 80
    assert u.parse_dimension("auto") is None
