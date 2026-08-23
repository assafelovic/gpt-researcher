"""get_relevant_images tolerates odd class attrs and None soup."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "gpt_researcher" / "scraper" / "utils.py"


class _Img:
    def __init__(self, src: str, classes):
        self._src = src
        self._classes = classes

    def __getitem__(self, key):
        if key == "src":
            return self._src
        raise KeyError(key)

    def get(self, key, default=None):
        if key == "class":
            return self._classes
        if key == "width":
            return default
        if key == "height":
            return default
        return default


def _load():
    bs4 = types.ModuleType("bs4")
    bs4.BeautifulSoup = object
    sys.modules.setdefault("bs4", bs4)
    parental = types.ModuleType("gpt_researcher")
    scraper = types.ModuleType("gpt_researcher.scraper")
    sys.modules.setdefault("gpt_researcher", parental)
    sys.modules.setdefault("gpt_researcher.scraper", scraper)
    spec = importlib.util.spec_from_file_location(
        "gpt_researcher.scraper.utils", MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class ImagesClassGuard(unittest.TestCase):
    def test_none_soup(self):
        mod = _load()
        self.assertEqual(mod.get_relevant_images(None, "https://ex.com"), [])

    def test_string_class_attr(self):
        mod = _load()
        soup = MagicMock()
        soup.find_all.return_value = [
            _Img("https://cdn.example/a.jpg", "header hero")
        ]
        out = mod.get_relevant_images(soup, "https://ex.com/")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["score"], 4)

    def test_non_sequence_class_attr(self):
        mod = _load()
        soup = MagicMock()
        soup.find_all.return_value = [_Img("https://cdn.example/b.jpg", 123)]
        out = mod.get_relevant_images(soup, "https://ex.com/")
        # falls through without class score; may still be included if no size req
        # with no width/height, score stays 0 and is included
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["score"], 0)


if __name__ == "__main__":
    unittest.main()
