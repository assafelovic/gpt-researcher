from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..actions.utils import stream_output
from ..actions.web_scraping import scrape_urls
from ..scraper.utils import get_image_hash  # Add this import

if TYPE_CHECKING:
    from gpt_researcher.agent import GPTResearcher


class BrowserManager:
    """Manages context for the researcher agent."""

    def __init__(self, researcher: GPTResearcher):
        self.researcher: GPTResearcher = researcher

    async def browse_urls(self, urls: list[str]) -> list[str]:
        """Scrape content from a list of URLs.

        Args:
            urls (list[str]): List of URLs to scrape.

        Returns:
            list[str]: List of scraped content results.
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "scraping_urls",
                f"🌐 Scraping content from {len(urls)} URLs...",
                self.researcher.websocket,
            )

        scraped_content: list[str]
        images: list[dict[str, Any]]
        scraped_content, images = scrape_urls(urls, self.researcher.cfg)
        self.researcher.add_research_sources(scraped_content)
        new_images: list[str] = self.select_top_images(images, k=4)  # Select top 2 images
        self.researcher.add_research_images(new_images)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "scraping_content",
                f"📄 Scraped {len(scraped_content)} pages of content",
                self.researcher.websocket,
            )
            await stream_output(
                "logs",
                "scraping_images",
                f"🖼️ Selected {len(new_images)} new images from {len(images)} total images",
                self.researcher.websocket,
                True,
                new_images,
            )
            await stream_output(
                "logs",
                "scraping_complete",
                "🌐 Scraping complete",
                self.researcher.websocket,
            )

        return scraped_content

    def select_top_images(
        self,
        images: list[dict[str, Any]],
        k: int = 2,
    ) -> list[str]:
        """Select most relevant images and remove duplicates based on image content.

        Args:
            images (list[dict[str, Any]]): List of image dictionaries with 'url' and 'score' keys.
            k (int): Number of top images to select if no high-score images are found.

        Returns:
            list[str]: List of selected image URLs.
        """
        unique_images: list[str] = []
        seen_hashes: set[str] = set()
        current_research_images: list[str] = self.researcher.get_research_images()

        # First, select all score 2 and 3 images

        for img in high_score_images + images:  # Process high-score images first, then all images
            img_hash = get_image_hash(img['url'])
            if img_hash and img_hash not in seen_hashes and img['url'] not in current_research_images:
        high_score_images: list[dict[str, Any]] = [
            img
            for img in images
            if img["score"] >= 2
        ]
                seen_hashes.add(img_hash)
                unique_images.append(img["url"])

                if len(unique_images) == k:
                    break

        return unique_images
