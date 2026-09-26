# Copyright (c) 2026 Shanlun. MIT License.
"""SmartPruner scraper backend for GPT Researcher.

Map-Expand token-efficient extraction: DOM noise removal + BM25 section
selection + a lightweight content map, with an on-demand expansion store
so pruned-away sections remain recoverable (no blind spots).

Pipeline:
  URL -> DOM noise removal -> section split -> BM25 budget selection
      -> context + content map (markdown)

stdlib-only: no third-party dependencies beyond `requests` (already a
GPT Researcher dependency).
"""

import logging

logger = logging.getLogger(__name__)


class SmartPrunerScraper:
    """Scraper backend using the bundled SmartPruner core.

    Typical reduction: 50-90% on documentation pages while keeping every
    section reachable through the expansion store (emitmap) attached to
    the returned content.
    """

    def __init__(self, link, session=None):
        self.link = link
        self.session = session

    def _fetch(self) -> str:
        """Fetch raw HTML. Uses the provided session when available,
        otherwise falls back to stdlib urllib."""
        if self.session is not None:
            resp = self.session.get(self.link)
            resp.raise_for_status()
            return resp.text
        import urllib.request

        req = urllib.request.Request(
            self.link, headers={"User-Agent": "Mozilla/5.0 (SmartPruner)"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")

    def scrape(self):
        """Fetch and extract the page with Map-Expand pruning.

        Returns:
            Tuple of (content, image_urls, title).
            content is markdown-ish text: selected sections + a content
            map listing every pruned section (title, tokens, key sentence)
            so the consuming LLM can request expansion when needed.
            image_urls is always [] — text extraction only.
        """
        try:
            from .core import SmartPruner

            html = self._fetch()
            if not html:
                return "", [], ""

            pruner = SmartPruner(budget_tokens=1500)
            result = pruner.prune(html, query="", doc_title="")
            title = ""
            if result.map_entries:
                title = result.map_entries[0].title

            if result.context:
                logger.info(
                    f"SmartPruner: {result.raw_tokens} -> "
                    f"{result.context_tokens} tokens "
                    f"({result.reduction:.0%} reduction, "
                    f"coverage={result.coverage:.2f})")

            return result.context, [], title

        except Exception as e:
            logger.error(f"SmartPruner failed for {self.link}: {e}")
            return "", [], ""
