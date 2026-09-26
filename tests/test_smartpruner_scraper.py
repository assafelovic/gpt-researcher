"""Tests for the SmartPruner scraper backend (stdlib-only)."""

import unittest

from gpt_researcher.scraper.smartpruner.core import SmartPruner
from gpt_researcher.scraper.smartpruner.smartpruner_scraper import (
    SmartPrunerScraper,
)

DOC = """
<html><head><title>Sample doc</title></head><body>
<nav class="main-nav"><a>Docs</a></nav>
<h1>Sample doc</h1>
<p>This intro paragraph explains the sample document and its purpose.</p>
<h2>Running things</h2>
<p>To run a task, call run_task() with the target name.</p>
<h2>Configuration</h2>
<p>Config options live in the config table and are documented elsewhere.</p>
<footer>copyright 2026</footer>
</body></html>
"""


class TestSmartPrunerCore(unittest.TestCase):
    def test_noise_removal_keeps_content(self):
        pruner = SmartPruner(budget_tokens=1500)
        res = pruner.prune(DOC, query="how do I run a task",
                           doc_title="Sample doc")
        self.assertIn("run_task()", res.context)
        self.assertNotIn("main-nav", res.context)
        self.assertNotIn("copyright", res.context)

    def test_map_lists_all_sections(self):
        pruner = SmartPruner(budget_tokens=1500)
        res = pruner.prune(DOC, query="configuration",
                           doc_title="Sample doc")
        titles = [e.title for e in res.map_entries]
        self.assertTrue(any("Running things" in t for t in titles))
        self.assertTrue(any("Configuration" in t for t in titles))

    def test_expansion_store_recovers_pruned_sections(self):
        pruner = SmartPruner(budget_tokens=30)   # force tight budget
        pruner.prune(DOC, query="configuration", doc_title="Sample doc")
        ids = pruner.store.list_ids()
        self.assertTrue(ids)
        expanded = pruner.store.expand(ids[0])
        self.assertIn("###", expanded)


class TestSmartPrunerScraper(unittest.TestCase):
    def test_interface_contract(self):
        scraper = SmartPrunerScraper("https://example.invalid/doc")
        # network unavailable in CI; just verify constructor + method exist
        self.assertTrue(callable(scraper.scrape))


if __name__ == "__main__":
    unittest.main()
