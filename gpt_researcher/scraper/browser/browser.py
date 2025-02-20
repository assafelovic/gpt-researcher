from __future__ import annotations

import logging
import os
import pickle
import random
import string
import time
import traceback
from pathlib import Path
from sys import platform
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from gpt_researcher.scraper.browser.processing.scrape_skills import (
    scrape_pdf_with_arxiv,
    scrape_pdf_with_pymupdf,
)
from gpt_researcher.scraper.utils import extract_title, get_relevant_images

if TYPE_CHECKING:
    import requests
    from selenium.webdriver.remote.webdriver import WebDriver


FILE_DIR = Path(__file__).parent.parent.absolute()


class BrowserScraper:
    """Browser Scraper."""

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        url: str,
        session: requests.Session | None = None,
        selenium_web_browser: str = "chrome",
        headless: bool = False,
        user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        use_browser_cookies: bool = False,
    ):
        self.url: str = url
        self.session: requests.Session | None = session
        self.selenium_web_browser: str = selenium_web_browser
        self.headless: bool = headless
        self.user_agent: str = user_agent
        self.driver: WebDriver | None = None
        self.use_browser_cookies: bool = use_browser_cookies
        self._import_selenium()  # Import only if used to avoid unnecessary dependencies
        self.cookie_filename = f"{self._generate_random_string(8)}.pkl"

    def scrape(self) -> tuple:
        if not self.url or not self.url.strip():
            self.logger.error("URL not specified")
            return "A URL was not specified, cancelling request to browse website.", [], ""

        try:
            self.setup_driver()
            self._visit_google_and_save_cookies()
            self._load_saved_cookies()
            self._add_header()

            text, image_urls, title = self.scrape_text_with_selenium()
        except Exception as e:
            self.logger.exception(f"An error occurred during scraping: {str(e)}")
            return (
                f"An error occurred: {e.__class__.__name__}: {e}\n\nStack trace:\n{traceback.format_exc()}",
                [],
                "",
            )
        else:
            return text, image_urls, title
        finally:
            if self.driver is not None:
                self.driver.quit()
            self._cleanup_cookie_file()

    def _import_selenium(self):
        try:
            global webdriver, By, EC, WebDriverWait, TimeoutException, WebDriverException
            from selenium import webdriver
            from selenium.common.exceptions import TimeoutException, WebDriverException
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.wait import WebDriverWait

            global ChromeOptions, FirefoxOptions, SafariOptions
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            from selenium.webdriver.safari.options import Options as SafariOptions
        except ImportError as e:
            self.logger.exception("Failed to import Selenium")
            self.logger.error("Please install Selenium and its dependencies to use BrowserScraper.")
            self.logger.error("You can install Selenium using pip:")
            self.logger.error("    pip install selenium")
            self.logger.error("If you're using a virtual environment, make sure it's activated.")
            raise ImportError(
                "Selenium is required but not installed. See error message above for installation instructions."
            ) from e

    def setup_driver(self) -> None:
        self.logger.debug(f"Setting up {self.selenium_web_browser} driver...")

        options_available: dict[str, type[ChromeOptions | FirefoxOptions | SafariOptions]] = {
            "chrome": ChromeOptions,
            "firefox": FirefoxOptions,
            "safari": SafariOptions,
        }

        options: ChromeOptions | FirefoxOptions | SafariOptions = options_available[
            self.selenium_web_browser
        ]()
        options.add_argument(f"user-agent={self.user_agent}")
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--enable-javascript")

        try:
            if self.selenium_web_browser == "firefox":
                self.driver = webdriver.Firefox(options=options)  # type: ignore[arg-type]
            elif self.selenium_web_browser == "safari":
                self.driver = webdriver.Safari(options=options)  # type: ignore[arg-type]
            else:  # chrome
                if platform == "linux" or platform == "linux2":
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--remote-debugging-port=9222")
                options.add_argument("--no-sandbox")
                options.add_experimental_option("prefs", {"download_restrictions": 3})  # type: ignore[attr-defined]
                self.driver = webdriver.Chrome(options=options)  # type: ignore[arg-type]

            if self.use_browser_cookies:
                self._load_browser_cookies()

        except Exception as e:
            self.logger.exception(
                f"Failed to set up {self.selenium_web_browser} driver: {e.__class__.__name__}: {e}"
            )
            self.logger.debug("Full stack trace:")
            self.logger.debug(traceback.format_exc())
            raise
        else:
            self.logger.debug(
                f"{self.selenium_web_browser.capitalize()} driver set up successfully."
            )

    def _load_saved_cookies(self):
        """Load saved cookies before visiting the target URL."""
        cookie_file = Path(self.cookie_filename)
        if cookie_file.exists():
            cookies = pickle.load(open(self.cookie_filename, "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)  # type: ignore[attr-defined]
        else:
            self.logger.warning("No saved cookies found.")

    def _load_browser_cookies(self):
        """Load cookies directly from the browser."""
        try:
            import browser_cookie3
        except ImportError:
            self.logger.exception(
                "browser_cookie3 is not installed. Please install it using: pip install browser_cookie3"
            )
            return

        if self.selenium_web_browser == "chrome":
            cookies = browser_cookie3.chrome()
        elif self.selenium_web_browser == "firefox":
            cookies = browser_cookie3.firefox()
        else:
            self.logger.error(f"Cookie loading not supported for {self.selenium_web_browser}")
            return

        assert self.driver is not None
        for cookie in cookies:
            self.driver.add_cookie(
                {"name": cookie.name, "value": cookie.value, "domain": cookie.domain}
            )

    def _cleanup_cookie_file(self):
        """Remove the cookie file."""
        cookie_file = Path(self.cookie_filename)
        if cookie_file.exists():
            try:
                os.remove(self.cookie_filename)
            except Exception as e:
                self.logger.exception(f"Failed to remove cookie file: {str(e)}")
        else:
            self.logger.warning("No cookie file found to remove.")

    def _generate_random_string(self, length):
        """Generate a random string of specified length."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _get_domain(self):
        """Extract domain from URL."""
        from urllib.parse import urlparse

        """Get domain from URL, removing 'www' if present"""
        domain = urlparse(self.url).netloc
        return domain[4:] if domain.startswith("www.") else domain

    def _visit_google_and_save_cookies(self):
        """Visit Google and save cookies before navigating to the target URL."""
        try:
            assert self.driver is not None
            self.driver.get("https://www.google.com")
            time.sleep(2)  # Wait for cookies to be set

            # Save cookies to a file
            cookies = self.driver.get_cookies()
            pickle.dump(cookies, open(self.cookie_filename, "wb"))

            self.logger.debug("Google cookies saved successfully.")
        except Exception as e:
            self.logger.exception(f"Failed to visit Google and save cookies: {str(e)}")

    def scrape_text_with_selenium(self) -> tuple:
        assert self.driver is not None
        self.driver.get(self.url)
        time.sleep(1)

        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            self.logger.exception("Timed out waiting for page to load")
            return "Page load timed out", [], ""

        self._scroll_to_bottom()

        if self.url.casefold().endswith(".pdf"):
            text = scrape_pdf_with_pymupdf(self.url)
            return text, [], ""
        elif "arxiv" in self.url.casefold():
            doc_num = self.url.split("/")[-1]
            text = scrape_pdf_with_arxiv(doc_num)
            return text, [], ""
        else:
            from bs4 import Tag

            page_source: Any = self.driver.execute_script("return document.body.outerHTML;")  # type: ignore[attr-defined]
            soup = BeautifulSoup(page_source, "html.parser")
            for script in soup(["script", "style"]):
                assert isinstance(script, Tag)
                script.extract()

            text = self.get_text(soup)
            image_urls = get_relevant_images(soup, self.url)
            title = extract_title(soup)

        lines: list[str] = list(line.strip() for line in text.splitlines())
        chunks: list[str] = list(phrase.strip() for line in lines for phrase in line.split("  "))
        text: str = "\n".join(chunk for chunk in chunks if chunk)
        return text, image_urls, title

    def get_text(
        self,
        soup: BeautifulSoup,
    ) -> str:
        """Get the relevant text from the soup with improved filtering."""
        text_elements: list[str] = []
        tags: list[str] = ["h1", "h2", "h3", "h4", "h5", "p", "li", "div", "span"]
        from bs4 import Tag

        for element in soup.find_all(tags):
            if not isinstance(element, Tag):
                continue
            # Skip empty elements
            if not element.text.strip():
                continue

            # Skip elements with very short text (likely buttons or links)
            if len(element.text.split()) < 3:
                continue

            # Check if the element is likely to be navigation or a menu
            assert isinstance(element.parent, Tag), "Element parent is not a Tag"
            parent_classes = element.parent.get("class", [])
            assert not isinstance(parent_classes, (type(None), str)), (
                "Parent classes are not a list or string"
            )
            if any(cls in ["nav", "menu", "sidebar", "footer"] for cls in parent_classes):
                continue

            # Remove excess whitespace and join lines
            cleaned_text: str = " ".join(element.text.split())

            # Add the cleaned text to our list of elements
            text_elements.append(cleaned_text)

        # Join all text elements with newlines
        return "\n\n".join(text_elements)

    def _scroll_to_bottom(self):
        """Scroll to the bottom of the page to load all content."""
        assert self.driver is not None
        last_height: int = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for content to load
            new_height: int = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def _scroll_to_percentage(self, ratio: float) -> None:
        """Scroll to a percentage of the page."""
        if ratio < 0 or ratio > 1:
            raise ValueError("Percentage should be between 0 and 1")
        assert self.driver is not None
        self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {ratio});")

    def _add_header(self) -> None:
        """Add a header to the website."""
        assert self.driver is not None
        self.driver.execute_script(open(f"{FILE_DIR}/browser/js/overlay.js").read())
