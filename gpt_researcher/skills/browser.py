from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gpt_researcher.actions.utils import stream_output
from gpt_researcher.actions.web_scraping import scrape_urls
from gpt_researcher.scraper.utils import get_image_hash

if TYPE_CHECKING:
    from gpt_researcher.agent import GPTResearcher


class BrowserManager:
    """Manages context for the researcher agent."""

    def __init__(
        self,
        researcher: GPTResearcher,
    ):
        self.researcher: GPTResearcher = researcher

    async def browse_urls(
        self,
        urls: list[str],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Scrape content from a list of URLs.

        Args:
        ----
            urls (list[str]): List of URLs to scrape.

        Returns:
        -------
            tuple[list[dict[str, Any]], list[dict[str, Any]]]: Tuple containing the scraped content and images.
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "scraping_urls",
                f"🌐 Scraping content from {len(urls)} URLs...",
                self.researcher.websocket,
            )

        scraped_content: tuple[list[dict[str, Any]], list[dict[str, Any]]] = scrape_urls(
            urls, self.researcher.research_config
        )
        self.researcher.add_research_sources(scraped_content[0])
        images: list[dict[str, Any]] = self.select_top_images(
            scraped_content[1], k=4
        )  # Select top 2 images
        self.researcher.add_research_images(images)

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
                f"🖼️ Selected {len(images)} new images from {len(images)} total images",
                self.researcher.websocket,
                metadata={"images": images},
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
    ) -> list[dict[str, Any]]:
        """Select most relevant images and remove duplicates based on image content.

        Args:
            images (list[dict[str, Any]]): List of image dictionaries with 'url' and 'score' keys.
            k (int): Number of top images to select if no high-score images are found.

        Returns:
            List[dict[str, Any]]: List of selected image dictionaries.
        """
        unique_images: list[dict[str, Any]] = []
        seen_hashes: set[str] = set()
        current_research_images: list[dict[str, Any]] = self.researcher.get_research_images()

        # First, select all score 2 and 3 images
        high_score_images: list[dict[str, Any]] = [img for img in images if img["score"] >= 2]

        for img in high_score_images + images:  # Process high-score images first, then all images
            img_hash: str | None = get_image_hash(img["url"])
            if (
                img_hash
                and img_hash not in seen_hashes
                and img["url"] not in current_research_images  # TODO: case sensitive??
            ):
                seen_hashes.add(img_hash)
                unique_images.append(img)

                if len(unique_images) == k:
                    break

        return unique_images
