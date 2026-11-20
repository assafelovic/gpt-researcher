import logging
import time

from bs4 import BeautifulSoup

from ..utils import get_relevant_images, extract_title, get_text_from_soup, clean_soup

logger = logging.getLogger(__name__)

# Response codes worth one retry: rate limiting and transient server errors.
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_CONTENT_BYTES = 10 * 1024 * 1024  # Skip pages larger than 10MB
TRANSPARENT_RESEARCH_USER_AGENT = (
    "GPT-Researcher/1.0 "
    "(+https://github.com/assafelovic/gpt-researcher; source retrieval)"
)


class BeautifulSoupScraper:

    def __init__(self, link, session=None):
        self.link = link
        self.session = session
        # Keep scrape()'s established three-item return value. Callers that
        # need diagnostics can inspect this optional, bounded reason instead.
        self.failure_reason = None

    def scrape(self):
        """Fetch the page and extract cleaned text, images and title.

        Returns:
            Tuple of (content, image_urls, title). Empty values are returned
            when the page cannot be fetched or yields no usable content.
        """
        response = self._fetch()
        if response is None:
            return "", [], ""

        try:
            # response.encoding defaults to ISO-8859-1 when the Content-Type
            # header omits a charset, which garbles many UTF-8 pages. Only
            # trust it when the server actually declared a charset; otherwise
            # let BeautifulSoup detect the encoding from the document itself.
            content_type = response.headers.get("Content-Type", "")
            declared_encoding = response.encoding if "charset" in content_type.lower() else None
            soup = BeautifulSoup(
                response.content, "lxml", from_encoding=declared_encoding
            )

            soup = clean_soup(soup)

            content = get_text_from_soup(soup)

            image_urls = get_relevant_images(soup, self.link)

            # Extract the title using the utility function
            title = extract_title(soup)

            return content, image_urls, title

        except Exception as e:
            logger.error(f"Error parsing {self.link}: {e}")
            return "", [], ""

    def _fetch(self):
        """GET the page, retrying once on transient failures.

        Returns the response on success, or None when the page is
        unreachable, an error status, or too large to be worth parsing.
        """
        if self.session is None:
            logger.warning(f"No session provided for {self.link}; cannot fetch")
            return None

        self.failure_reason = None
        retry_with_transparent_identity = False
        for attempt in (1, 2):
            request_kwargs = {"timeout": 10}
            if retry_with_transparent_identity:
                request_kwargs["headers"] = {
                    "User-Agent": TRANSPARENT_RESEARCH_USER_AGENT,
                }
            try:
                response = self.session.get(self.link, **request_kwargs)
            except Exception as e:
                logger.warning(f"Request failed for {self.link} (attempt {attempt}): {e}")
                if attempt == 1:
                    time.sleep(1)
                    continue
                return None

            if response.status_code in RETRYABLE_STATUS_CODES and attempt == 1:
                logger.warning(
                    f"Got HTTP {response.status_code} for {self.link}, retrying once"
                )
                time.sleep(1)
                continue

            if response.status_code == 403 and attempt == 1:
                logger.warning(
                    f"Got HTTP 403 for {self.link}, retrying once with a "
                    "transparent GPT Researcher identity"
                )
                retry_with_transparent_identity = True
                continue

            if response.status_code >= 400:
                # Don't parse error/paywall pages as if they were content
                self.failure_reason = f"HTTP_{response.status_code}"
                logger.warning(f"Got HTTP {response.status_code} for {self.link}, skipping")
                return None

            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    length_val = int(str(content_length).strip())
                except (TypeError, ValueError):
                    length_val = None
                if length_val is not None and length_val > MAX_CONTENT_BYTES:
                    logger.warning(
                        f"Content too large for {self.link} ({content_length} bytes), skipping"
                    )
                    return None

            return response

        return None
