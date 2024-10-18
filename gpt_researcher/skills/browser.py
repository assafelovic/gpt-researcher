import asyncio
from typing import List, Dict, Optional, Set

from ..actions.utils import stream_output
from ..actions.web_scraping import scrape_urls


class BrowserManager:
    """Manages context for the researcher agent."""

    def __init__(self, researcher):
        self.researcher = researcher

    async def browse_urls(self, urls: List[str]) -> List[Dict]:
        """
        Scrape content from a list of URLs.

        Args:
            urls (List[str]): List of URLs to scrape.

        Returns:
            List[Dict]: List of scraped content results.
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "scraping_urls",
                f"🌐 Scraping content from {len(urls)} URLs...",
                self.researcher.websocket,
            )

        scraped_content = scrape_urls(urls, self.researcher.cfg)

        return scraped_content
