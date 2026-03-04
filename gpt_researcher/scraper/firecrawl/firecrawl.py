import asyncio
import logging
import os

from bs4 import BeautifulSoup

from ..utils import get_relevant_images

logger = logging.getLogger(__name__)

# Module-level semaphore for API concurrency limiting.
# Shared across all FireCrawl instances to respect API rate limits.
_api_semaphore: asyncio.Semaphore | None = None
_semaphore_limit: int = 0


def _get_api_semaphore() -> asyncio.Semaphore:
    """Get or create the module-level API concurrency semaphore.

    The concurrency limit is controlled by the ``FIRECRAWL_CONCURRENCY``
    environment variable (default: ``2``, matching Firecrawl Free Tier's
    2 concurrent browser limit).
    """
    global _api_semaphore, _semaphore_limit
    limit = int(os.environ.get("FIRECRAWL_CONCURRENCY", "2"))
    # Re-create if the configured limit changed (e.g. between tests).
    if _api_semaphore is None or limit != _semaphore_limit:
        _api_semaphore = asyncio.Semaphore(limit)
        _semaphore_limit = limit
    return _api_semaphore


class FireCrawl:

    # Default retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_BASE_DELAY = 2.0  # seconds

    def __init__(self, link, session=None):
        self.link = link
        self.session = session
        from firecrawl import FirecrawlApp
        self.firecrawl = FirecrawlApp(api_key=self.get_api_key(), api_url=self.get_server_url())
        self.max_retries = int(os.environ.get("FIRECRAWL_MAX_RETRIES", str(self.DEFAULT_MAX_RETRIES)))
        self.retry_base_delay = float(os.environ.get("FIRECRAWL_RETRY_BASE_DELAY", str(self.DEFAULT_RETRY_BASE_DELAY)))

    def get_api_key(self) -> str:
        """
        Gets the FireCrawl API key
        Returns:
        Api key (str)
        """
        try:
            api_key = os.environ["FIRECRAWL_API_KEY"]
        except KeyError:
            raise Exception(
                "FireCrawl API key not found. Please set the FIRECRAWL_API_KEY environment variable.")
        return api_key

    def get_server_url(self) -> str:
        """
        Gets the FireCrawl server URL.
        Default to official FireCrawl server ('https://api.firecrawl.dev').
        Returns:
        server url (str)
        """
        try:
            server_url = os.environ["FIRECRAWL_SERVER_URL"]
        except KeyError:
            server_url = 'https://api.firecrawl.dev'
        return server_url

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if an exception indicates a rate limit (HTTP 429) error."""
        error_str = str(error).lower()
        return "429" in error_str or "rate limit" in error_str

    def _scrape_once(self) -> tuple:
        """Execute a single FireCrawl scrape attempt.

        Returns:
            Tuple of (content, image_urls, title). Returns ("", [], "") on
            failure.
        """
        # Fixed: Changed from scrape_url() to scrape() to match FireCrawl SDK v4.6.0+
        response = self.firecrawl.scrape(url=self.link, formats=["markdown"])

        # Check if the page has been scraped successfully
        # Fixed: Access metadata attributes directly (not as dict keys)
        if response.metadata and response.metadata.error:
            raise RuntimeError(f"Scrape failed: {response.metadata.error}")
        elif response.metadata and response.metadata.status_code and response.metadata.status_code != 200:
            raise RuntimeError(f"Scrape failed with status code: {response.metadata.status_code}")

        # Extract the content (markdown) and title from FireCrawl response
        # Fixed: Access attributes directly (not as dict keys)
        content = response.markdown if response.markdown else ""
        title = response.metadata.title if response.metadata and response.metadata.title else ""

        # Parse the HTML content of the response to create a BeautifulSoup object for the utility functions
        response_bs = self.session.get(self.link, timeout=4)
        soup = BeautifulSoup(
            response_bs.content, "lxml", from_encoding=response_bs.encoding
        )

        # Get relevant images using the utility function
        image_urls = get_relevant_images(soup, self.link)

        return content, image_urls, title

    def scrape(self) -> tuple:
        """
        This function extracts content and title from a specified link using the FireCrawl Python SDK,
        images from the link are extracted using the functions from `gpt_researcher/scraper/utils.py`.

        Returns:
          The `scrape` method returns a tuple containing the extracted content, a list of image URLs, and
        the title of the webpage specified by the `self.link` attribute. It uses the FireCrawl Python SDK to
        extract and clean content from the webpage. If any exception occurs during the process, an error
        message is printed and an empty result is returned.
        """

        try:
            return self._scrape_once()
        except Exception as e:
            logger.error("Error scraping %s: %s", self.link, e)
            return "", [], ""

    async def scrape_async(self) -> tuple:
        """Async scrape with concurrency limiting and retry with exponential backoff.

        This method:
        1. Acquires the module-level semaphore to limit concurrent Firecrawl API
           calls (controlled by ``FIRECRAWL_CONCURRENCY``, default 2).
        2. Retries on rate-limit errors (HTTP 429) and empty/short content with
           exponential backoff (controlled by ``FIRECRAWL_MAX_RETRIES``, default 3).

        Returns:
            Tuple of (content, image_urls, title).
        """
        semaphore = _get_api_semaphore()
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            async with semaphore:
                try:
                    content, image_urls, title = await asyncio.get_running_loop().run_in_executor(
                        None, self._scrape_once
                    )

                    # Treat empty / very short content as a transient failure
                    # (Firecrawl may silently return empty when rate-limited)
                    if len(content) < 100 and attempt < self.max_retries:
                        logger.warning(
                            "FireCrawl returned short content (%d chars) for %s, "
                            "retrying (%d/%d)...",
                            len(content), self.link, attempt + 1, self.max_retries,
                        )
                        delay = self.retry_base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                        continue

                    return content, image_urls, title

                except Exception as e:
                    last_error = e
                    if attempt < self.max_retries and self._is_rate_limit_error(e):
                        delay = self.retry_base_delay * (2 ** attempt)
                        logger.warning(
                            "FireCrawl rate limited for %s, retrying in %.1fs "
                            "(%d/%d)...",
                            self.link, delay, attempt + 1, self.max_retries,
                        )
                        await asyncio.sleep(delay)
                        continue

                    # Non-retryable error or retries exhausted
                    break

        logger.error(
            "FireCrawl failed for %s after %d attempts: %s",
            self.link, self.max_retries + 1, last_error,
        )
        return "", [], ""
