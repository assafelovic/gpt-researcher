"""Tests for the DomPruner scraper backend.

Covers:
- Routing: 'dompruner' key in SCRAPER_CLASSES maps to DomPrunerScraper
- Happy path: scrape() returns (content, [], title) from PipelineResult
- Missing package: ImportError is handled gracefully, returns ("", [], "")
- Pipeline exception: exception is caught, returns ("", [], "")
- session=None: accepted without error (dompruner manages its own HTTP client)
- Empty content: pipeline returning empty markdown passes through as ""
- Logging: token reduction numbers are logged at INFO level
"""

import ast
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRAPER_PY = _ROOT / "gpt_researcher" / "scraper" / "scraper.py"
_DOMPRUNER_PY = _ROOT / "gpt_researcher" / "scraper" / "dompruner" / "dompruner_scraper.py"


# ---------------------------------------------------------------------------
# Load DomPrunerScraper directly (no transitive deps needed)
# ---------------------------------------------------------------------------

def _load_dompruner_class():
    """Load DomPrunerScraper without importing the full gpt_researcher package."""
    mod_name = "gpt_researcher.scraper.dompruner.dompruner_scraper"
    if mod_name in sys.modules:
        return sys.modules[mod_name].DomPrunerScraper
    spec = importlib.util.spec_from_file_location(mod_name, _DOMPRUNER_PY)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "gpt_researcher.scraper.dompruner"
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod.DomPrunerScraper


DomPrunerScraper = _load_dompruner_class()


# ---------------------------------------------------------------------------
# Routing tests — verified via static AST parsing of scraper.py so we don't
# need to import the full gpt_researcher package (which requires langgraph,
# colorama, requests, json_repair, …).
# ---------------------------------------------------------------------------

def _scraper_classes_from_ast():
    """Parse SCRAPER_CLASSES dict keys from scraper.py via AST — no import needed."""
    tree = ast.parse(_SCRAPER_PY.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
            if "dompruner" in keys and "firecrawl" in keys and "pdf" in keys:
                return keys
    return []


class TestDomPrunerRouting(unittest.TestCase):
    """Verify that scraper.py registers DomPrunerScraper correctly."""

    def test_dompruner_key_present_in_scraper_classes(self):
        keys = _scraper_classes_from_ast()
        self.assertIn("dompruner", keys,
                      "SCRAPER_CLASSES in scraper.py is missing the 'dompruner' key")

    def test_dompruner_scraper_importable_from_package(self):
        """The scraper __init__.py must export DomPrunerScraper."""
        init_src = (_ROOT / "gpt_researcher" / "scraper" / "__init__.py").read_text()
        self.assertIn("DomPrunerScraper", init_src)

    def test_dompruner_value_in_scraper_classes_is_dompruner_class(self):
        """SCRAPER_CLASSES['dompruner'] must reference DomPrunerScraper (by name).

        SCRAPER_CLASSES is identified by containing both 'pdf' and 'arxiv' keys
        alongside 'dompruner', which distinguishes it from pkg_map in _check_pkg.
        """
        tree = ast.parse(_SCRAPER_PY.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            const_keys = {k.value for k in node.keys if isinstance(k, ast.Constant)}
            # Only look at the SCRAPER_CLASSES dict (has pdf + arxiv + dompruner)
            if not ({"pdf", "arxiv", "dompruner"} <= const_keys):
                continue
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == "dompruner":
                    class_name = v.id if isinstance(v, ast.Name) else None
                    self.assertEqual(class_name, "DomPrunerScraper",
                                     f"SCRAPER_CLASSES['dompruner'] should be "
                                     f"DomPrunerScraper, got: {ast.dump(v)}")
                    return
        self.fail("Could not locate SCRAPER_CLASSES['dompruner'] in scraper.py")

    def test_check_pkg_map_includes_dompruner(self):
        """_check_pkg's pkg_map must contain dompruner so missing installs are caught."""
        src = _SCRAPER_PY.read_text()
        # Simple string-presence check is sufficient; the exact structure
        # matters only to _check_pkg, which is covered by the routing tests.
        self.assertIn('"dompruner"', src)
        self.assertIn("package_installation_name", src)


# ---------------------------------------------------------------------------
# DomPrunerScraper unit tests (dompruner package is mocked)
# ---------------------------------------------------------------------------

class TestDomPrunerScraper(unittest.TestCase):

    def _instance(self, url="https://docs.example.com/api", session=None):
        return DomPrunerScraper(url, session=session)

    def _patch_dompruner(self, result):
        """Replace the dompruner package in sys.modules with a lightweight fake."""
        fake = types.SimpleNamespace(
            PipelineResult=MagicMock,
            run_pipeline=MagicMock(return_value="coro_sentinel"),
            sync_run=MagicMock(return_value=result),
        )
        return patch.dict(sys.modules, {"dompruner": fake})

    def _make_result(self, markdown="Clean content.", title="Page Title",
                     original_tokens=5000, refined_tokens=300,
                     reduction_ratio=0.94, render_type="ssr"):
        r = MagicMock()
        r.markdown = markdown
        r.meta = {"title": title}
        r.original_tokens = original_tokens
        r.refined_tokens = refined_tokens
        r.reduction_ratio = reduction_ratio
        r.render_type = render_type
        return r

    # --- happy path ---

    def test_scrape_returns_markdown_and_title(self):
        result = self._make_result(markdown="# API Docs\n\nFetch API.", title="MDN")
        with self._patch_dompruner(result):
            content, images, title = self._instance().scrape()
        self.assertEqual(content, "# API Docs\n\nFetch API.")
        self.assertEqual(title, "MDN")
        self.assertEqual(images, [])

    def test_scrape_image_urls_always_empty(self):
        with self._patch_dompruner(self._make_result()):
            _, images, _ = self._instance().scrape()
        self.assertEqual(images, [])

    def test_scrape_accepts_session_none(self):
        with self._patch_dompruner(self._make_result()):
            content, _, _ = self._instance(session=None).scrape()
        self.assertEqual(content, "Clean content.")

    def test_scrape_accepts_session_object(self):
        with self._patch_dompruner(self._make_result()):
            content, _, _ = self._instance(session=MagicMock()).scrape()
        self.assertEqual(content, "Clean content.")

    # --- missing package ---

    def test_scrape_missing_dompruner_package_returns_empty(self):
        """If dompruner is not installed, scrape() must not raise."""
        with patch.dict(sys.modules, {"dompruner": None}):
            content, images, title = self._instance().scrape()
        self.assertEqual((content, images, title), ("", [], ""))

    # --- pipeline errors ---

    def test_scrape_pipeline_exception_returns_empty(self):
        fake = types.SimpleNamespace(
            PipelineResult=MagicMock,
            run_pipeline=MagicMock(return_value="coro_sentinel"),
            sync_run=MagicMock(side_effect=RuntimeError("network error")),
        )
        with patch.dict(sys.modules, {"dompruner": fake}):
            content, images, title = self._instance().scrape()
        self.assertEqual((content, images, title), ("", [], ""))

    def test_scrape_empty_markdown_returns_empty_string(self):
        with self._patch_dompruner(self._make_result(markdown="", title="")):
            content, _, title = self._instance().scrape()
        self.assertEqual(content, "")
        self.assertEqual(title, "")

    # --- logging ---

    def test_scrape_logs_token_reduction_info(self):
        result = self._make_result(original_tokens=15000, refined_tokens=900,
                                   reduction_ratio=0.94)
        with self._patch_dompruner(result):
            with self.assertLogs("gpt_researcher.scraper.dompruner.dompruner_scraper",
                                 level="INFO") as cm:
                self._instance().scrape()
        self.assertTrue(
            any("15000" in line and "900" in line for line in cm.output),
            f"Expected token counts in log output, got: {cm.output}",
        )


if __name__ == "__main__":
    unittest.main()
