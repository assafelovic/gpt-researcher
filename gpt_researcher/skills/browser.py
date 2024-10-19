from typing import List, Dict, Optional, Set
import hashlib
import re

from ..actions.utils import stream_output
from ..actions.web_scraping import scrape_urls


class BrowserManager:
    """Manages context for the researcher agent."""

    def __init__(self, researcher):
        self.researcher = researcher
        self.research_sources = []
        self.research_images = []

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

        scraped_content, images = scrape_urls(urls, self.researcher.cfg)
        self.research_sources.extend(scraped_content)
        new_images = self.select_top_images(images, k=2)  # Select top 2 images
        self.research_images.extend(new_images)

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
            )
            await stream_output(
                "logs",
                "scraping_complete",
                f"🌐 Scraping complete",
                self.researcher.websocket,
            )

        return scraped_content

    def select_top_images(self, images: List[Dict], k: int = 2) -> List[str]:
        """
        Select top k images and remove duplicates.

        Args:
            images (List[Dict]): List of image dictionaries with 'url' keys.
            k (int): Number of top images to select.

        Returns:
            List[str]: List of selected top image URLs.
        """
        # Remove duplicates based on image URL
        unique_images = []
        image_hashes = set()

        for img in images:
            img_hash = hashlib.md5(img['url'].encode()).hexdigest()
            if img_hash not in image_hashes and img_hash not in {hashlib.md5(existing_img.encode()).hexdigest() for existing_img in self.research_images}:
                image_hashes.add(img_hash)
                unique_images.append(img['url'])

                if len(unique_images) == k:
                    break

        return unique_images

    def get_research_sources(self) -> List[Dict]:
        """
        Get the list of research sources.

        Returns:
            List[Dict]: List of research sources.
        """
        return self.research_sources

    def get_research_images(self) -> List[str]:
        """
        Get the list of selected research image URLs.

        Returns:
            List[str]: List of selected research image URLs.
        """
        return self.research_images
