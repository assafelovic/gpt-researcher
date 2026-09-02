"""DomPruner scraper backend for GPT Researcher.

Reduces LLM context tokens by 90%+ on documentation and article pages
using DOM AST extraction and optional BM25 section filtering.

Pipeline:
  URL → DOM AST noise removal (nav/footer/scripts) → BM25 section filter
      → Markdown serialisation → token budget

Requires: pip install dompruner
"""

import logging

logger = logging.getLogger(__name__)


class DomPrunerScraper:
    """Scraper backend that uses dompruner for token-efficient extraction.

    Typical reduction: 90–99% on documentation sites, with original text
    preserved in retained sections (no LLM summarisation).
    """

    def __init__(self, link, session=None):
        self.link = link
        # session is accepted for interface compatibility but dompruner
        # manages its own HTTP client (httpx, UA rotation, SSG path).

    def scrape(self):
        """Fetch and extract the page with DOM AST pruning.

        Returns:
            Tuple of (content, image_urls, title).
            image_urls is always [] — dompruner returns text/markdown only.
        """
        try:
            from dompruner import PipelineResult, sync_run, run_pipeline
        except ImportError:
            logger.error(
                "dompruner is not installed. Run: pip install dompruner"
            )
            return "", [], ""

        try:
            result: PipelineResult = sync_run(run_pipeline(self.link, query=""))

            content = result.markdown
            title = result.meta.get("title", "")

            if content:
                logger.info(
                    f"DomPruner: {result.original_tokens} → {result.refined_tokens} tokens "
                    f"({result.reduction_ratio:.0%} reduction) [{result.render_type}]"
                )

            return content, [], title

        except Exception as e:
            logger.error(f"DomPruner failed for {self.link}: {e}")
            return "", [], ""
