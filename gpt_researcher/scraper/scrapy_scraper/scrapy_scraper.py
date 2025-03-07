from __future__ import annotations

import json
import logging
import os
import tempfile

from typing import Any, ClassVar
from urllib.parse import urlparse

import scrapy

from bs4 import BeautifulSoup
from bs4.element import Tag
from scrapy.crawler import CrawlerProcess
from scrapy.http.response.html import HtmlResponse

from gpt_researcher.scraper.scraper_abc import BaseScraperABC
from gpt_researcher.scraper.utils import get_relevant_images
from gpt_researcher.utils.logger import get_formatted_logger

logger: logging.Logger = get_formatted_logger(__name__)


class ScrapySpider(scrapy.Spider):
    """Scrapy spider for extracting content from a webpage.

    This spider is designed to extract the main content, images, and title
    from a single webpage. It uses CSS selectors to target common content
    containers and falls back to the entire body if specific containers
    aren't found.
    """

    name = "gpt_researcher_spider"

    def __init__(
        self,
        url: str,
        output_file: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the spider with a URL and output file.

        Args:
            url: The URL to scrape
            output_file: Path to save the scraped data
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.start_urls: list[str] = [url]
        self.output_file: str = output_file
        self.results: dict[str, Any] = {"content": "", "images": [], "title": ""}

    def parse(self, response: HtmlResponse) -> None:
        """Parse the response and extract content.

        This method extracts the title, main content, and images from the webpage.
        It tries to target specific content containers first and falls back to
        the entire body if needed.

        Args:
            response: The HTTP response from Scrapy
        """
        # Extract title
        self.results["title"] = response.css("title::text").get() or ""

        # Extract main content
        content_selectors: list[str] = [
            "article",
            "main",
            ".content",
            "#content",
            ".post",
            ".article",
            ".post-content",
            ".entry-content",
            ".main-content",
            "#main",
            "#article",
            ".body",
            ".page-content",
            ".text",
            ".story",
            ".story-content",
            ".news-content",
        ]

        content: str = ""
        for selector in content_selectors:
            if response.css(selector):
                content = " ".join(response.css(f"{selector} ::text").getall())
                break

        # If no content found with specific selectors, get body text
        if not content:
            # Remove script, style, and other non-content elements
            content = " ".join(response.css("body ::text").getall())

        self.results["content"] = content

        # Extract images
        image_urls: list[dict[str, Any]] = []
        for img in response.css("img"):
            src: str | None = img.css("::attr(src)").get()
            if src:
                # Handle relative URLs
                if not src.startswith(("http://", "https://")):
                    src = response.urljoin(src)

                alt: str | None = img.css("::attr(alt)").get() or ""
                image_urls.append({"url": src, "alt": alt})

        self.results["images"] = image_urls

        # Save results to file
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f)


class ScrapyScraper(BaseScraperABC):
    """Scraper implementation using Scrapy.

    This class provides an interface to scrape web content using Scrapy,
    following the same interface as other scrapers in the GPT Researcher project.
    """

    MODULE_NAME: ClassVar[str] = "scrapy"

    def __init__(
        self,
        link: str,
        session: Any | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the ScrapyScraper.

        Args:
            link: The URL to scrape
            session: Optional session object (not used by Scrapy but kept for interface compatibility)
            scraper: Optional scraper type (not used but kept for interface compatibility)
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self.link: str = link
        self.session: Any | None = session
        self.args: Any = args
        self.kwargs: Any = kwargs

    def scrape(self) -> tuple[str, list[dict[str, Any]], str]:
        """Scrape content from a webpage using Scrapy.

        This method configures and runs a Scrapy spider to extract content
        from the specified URL. It handles the temporary file storage for
        data exchange between the Scrapy process and the main application.

        Returns:
            A tuple containing:
            - The extracted content as a string
            - A list of image information dictionaries
            - The page title
        """
        # Create a temporary file to store the scraped data
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp:
            output_file = temp.name

        try:
            # Create a crawler process with aggressive settings for speed and maximum data extraction
            process = CrawlerProcess(
                {
                    # Use a modern browser user agent
                    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    # Ignore robots.txt for unrestricted crawling
                    "ROBOTSTXT_OBEY": False,
                    # Reduce logging to speed things up
                    "LOG_LEVEL": "ERROR",
                    # Enable cookies for accessing all content
                    "COOKIES_ENABLED": True,
                    # Maximize concurrent requests for speed
                    "CONCURRENT_REQUESTS": 16,
                    "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
                    # Minimize delay between requests
                    "DOWNLOAD_DELAY": 0,
                    # Retry aggressively on failure
                    "RETRY_ENABLED": True,
                    "RETRY_TIMES": 5,
                    "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429, 403, 400],
                    # Set longer timeout for content-heavy pages
                    "DOWNLOAD_TIMEOUT": 60,
                    # Disable telnet console for security and performance
                    "TELNETCONSOLE_ENABLED": False,
                    # Disable auto-throttling for maximum speed
                    "AUTOTHROTTLE_ENABLED": False,
                    # Download maximum content
                    "URLLENGTH_LIMIT": 5000,
                    "REDIRECT_ENABLED": True,
                    "REDIRECT_MAX_TIMES": 5,
                    # Handle compression for faster downloads
                    "COMPRESSION_ENABLED": True,
                    # Optimize request priority for faster results
                    "DEPTH_PRIORITY": 1,
                    "SCHEDULER_DISK_QUEUE": "scrapy.squeues.PickleFifoDiskQueue",
                    "SCHEDULER_MEMORY_QUEUE": "scrapy.squeues.FifoMemoryQueue",
                }
            )

            # Run the spider
            process.crawl(ScrapySpider, url=self.link, output_file=output_file)
            process.start()

            # Load the scraped data
            with open(output_file, "r", encoding="utf-8") as f:
                results: dict[str, Any] = json.load(f)

            content: str = results.get("content", "")
            raw_images: list[dict[str, Any]] = results.get("images", [])
            title: str = results.get("title", "")

            # Create a fallback title if none was found
            fallback_title: str = os.path.basename(urlparse(self.link).path) or self.link

            # Process images to match expected format
            # Create a BeautifulSoup object for image processing
            image_soup = BeautifulSoup("", "html.parser")
            processed_images: list[dict[str, Any]] = []

            # Convert raw images to the format expected by get_relevant_images
            for img in raw_images:
                img_tag: Tag = image_soup.new_tag("img")
                img_tag["src"] = img["url"]
                if img.get("alt"):
                    img_tag["alt"] = img["alt"]
                image_soup.append(img_tag)

            # Process images using the utility function
            if raw_images:
                processed_images = get_relevant_images(image_soup, self.link)

            # Ensure we have a valid title (not None)
            final_title: str = title if title else fallback_title

            return content, processed_images, final_title

        except Exception as e:
            logger.exception(f"Error scraping with Scrapy: {e}")
            # Create a fallback title from the URL
            fallback_title = os.path.basename(urlparse(self.link).path) or self.link
            return "", [], fallback_title

        finally:
            # Clean up the temporary file
            if os.path.exists(output_file):
                os.unlink(output_file)
