from __future__ import annotations
import importlib.util
from pathlib import Path

def _load():
    path = Path(__file__).resolve().parents[1] / "gpt_researcher" / "scraper" / "utils.py"
    spec = importlib.util.spec_from_file_location("su", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_none_soup():
    assert _load().get_text_from_soup(None) == ""
