from __future__ import annotations

import asyncio
import logging
import math
import random

from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncGenerator, ClassVar, Literal, cast
from urllib.parse import urlparse

import requests

from bs4 import BeautifulSoup

from gpt_researcher.scraper.utils import (
    clean_soup,
    extract_title,
    get_relevant_images,
    get_text_from_soup,
)
from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging

    import requests

    from zendriver import Tab


class NoDriverScraper:
    logger: ClassVar[logging.Logger] = get_formatted_logger(__name__)  # pyright: ignore[reportCallIssue]
    max_browsers: ClassVar[int] = 3
    browser_load_threshold: ClassVar[int] = 5
    browsers: ClassVar[set[NoDriverScraper.Browser]] = set()
    browsers_lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    @staticmethod
    def get_domain(url: str) -> str:
        domain: str = urlparse(url).netloc
        parts: list[str] = domain.split(".")
        if len(parts) > 2:
            domain = ".".join(parts[-2:])
        return domain

    class Browser:
        def __init__(
            self,
            driver: zendriver.Browser,
        ):
            self.driver: zendriver.Browser = driver
            self.processing_count: int = 0
            self.has_blank_page: bool = True
            self.allowed_requests_times: dict[str, float] = {}
            self.domain_semaphores: dict[str, asyncio.Semaphore] = {}
            self.tab_mode: bool = True
            self.max_scroll_percent: int = 500
            self.stopping: bool = False

        async def get(self, url: str) -> zendriver.Tab:
            self.processing_count += 1
            try:
                async with self.rate_limit_for_domain(url):
                    new_window: bool = not self.has_blank_page
                    self.has_blank_page = False
                    if self.tab_mode:
                        return await self.driver.get(url, new_tab=new_window)
                    else:
                        return await self.driver.get(url, new_window=new_window)
            except Exception:
                self.processing_count -= 1
                raise

        async def scroll_page_to_bottom(
            self,
            page: zendriver.Tab,
        ):
            total_scroll_percent: int = 0
            while True:
                # in tab mode, we need to bring the tab to front before scrolling to load the page content properly
                if self.tab_mode:
                    await page.bring_to_front()
                scroll_percent: int = random.randrange(46, 97)
                total_scroll_percent += scroll_percent
                await page.scroll_down(scroll_percent)
                await self.wait_or_timeout(page, "idle", 2)
                await page.sleep(random.uniform(0.23, 0.56))

                if total_scroll_percent >= self.max_scroll_percent:
                    break

                if cast(
                    bool,
                    await page.evaluate("window.innerHeight + window.scrollY >= document.scrollingElement.scrollHeight"),
                ):
                    break

        async def wait_or_timeout(
            self,
            page: "zendriver.Tab",
            until: Literal["complete", "idle"] = "idle",
            timeout: float = 3,
        ):
            try:
                if until == "idle":
                    await asyncio.wait_for(page.wait(), timeout)
                else:
                    timeout = math.ceil(timeout)
                    await page.wait_for_ready_state(until, timeout=timeout)
            except asyncio.TimeoutError:
                NoDriverScraper.logger.debug(f"timeout waiting for {until} after {timeout} seconds")

        async def close_page(
            self,
            page: "zendriver.Tab",
        ):
            try:
                await page.close()
            except Exception as e:
                NoDriverScraper.logger.error(f"Failed to close page: {e}")
            finally:
                self.processing_count -= 1

        @asynccontextmanager
        async def rate_limit_for_domain(
            self,
            url: str,
        ) -> AsyncGenerator[None, Any]:
            semaphore: asyncio.Semaphore | None = None
            try:
                domain: str = NoDriverScraper.get_domain(url)

                semaphore = self.domain_semaphores.get(domain)
                if not semaphore:
                    semaphore = asyncio.Semaphore(1)
                    self.domain_semaphores[domain] = semaphore

                was_locked = semaphore.locked()
                async with semaphore:
                    if was_locked:
                        await asyncio.sleep(random.uniform(0.6, 1.2))
                    yield

            except Exception as e:
                # Log error but don't block the request
                NoDriverScraper.logger.warning(f"Rate limiting error for {url}: {str(e)}")

        async def stop(self):
            if self.stopping:
                return
            self.stopping = True
            await self.driver.stop()

    @classmethod
    async def get_browser(
        cls,
        headless: bool = False,
    ) -> NoDriverScraper.Browser:
        async def create_browser() -> NoDriverScraper.Browser:
            try:
                global zendriver
                import zendriver  # pyright: ignore[reportMissingImports]
            except ImportError:
                raise ImportError("The zendriver package is required to use NoDriverScraper. Please install it with: pip install zendriver")

            config = zendriver.Config(
                headless=headless,
                browser_connection_timeout=1,
            )
            driver: zendriver.Browser = await zendriver.start(config)
            browser: NoDriverScraper.Browser = cls.Browser(driver)
            cls.browsers.add(browser)
            return browser

        async with cls.browsers_lock:
            if len(cls.browsers) == 0:
                # No browsers available, create new one
                return await create_browser()

            # Load balancing: Get browser with lowest number of tabs
            browser: NoDriverScraper.Browser = min(cls.browsers, key=lambda b: b.processing_count)

            # If all browsers are heavily loaded and we can create more
            if browser.processing_count >= cls.browser_load_threshold and len(cls.browsers) < cls.max_browsers:
                return await create_browser()

            return browser

    @classmethod
    async def release_browser(
        cls,
        browser: NoDriverScraper.Browser,
    ):
        async with cls.browsers_lock:
            if browser and browser.processing_count <= 0:
                try:
                    await browser.stop()
                except Exception as e:
                    NoDriverScraper.logger.error(f"Failed to release browser: {e}")
                finally:
                    cls.browsers.discard(browser)

    def __init__(
        self,
        url: str,
        session: requests.Session | None = None,
    ):
        self.url: str = url
        self.session: requests.Session | None = session
        self.debug: bool = False

    async def scrape_async(self) -> tuple[str, list[str], str]:
        """Returns tuple of (text, image_urls, title)."""
        if not self.url:
            return (
                "A URL was not specified, cancelling request to browse website.",
                [],
                "",
            )

        browser: NoDriverScraper.Browser | None = None
        page: Tab | None = None
        try:
            try:
                browser = await self.get_browser()
            except ImportError as e:
                self.logger.error(f"Failed to initialize browser: {str(e)}")
                return str(e), [], ""

            page = await browser.get(self.url)
            await browser.wait_or_timeout(page, "complete", 2)
            # wait for potential redirection
            await page.sleep(random.uniform(0.3, 0.7))
            await browser.wait_or_timeout(page, "idle", 2)

            await browser.scroll_page_to_bottom(page)
            html: str = await page.get_content()
            soup: BeautifulSoup = BeautifulSoup(html, "lxml")
            clean_soup(soup)
            text: str = get_text_from_soup(soup)
            images: list[dict[str, Any]] = get_relevant_images(soup, self.url)
            image_urls: list[str] = [image.get("url", image.get("href", "")) for image in images]
            title: str | None = extract_title(soup)

            if len(text) < 200:
                self.logger.warning(f"Content is too short from {self.url}. Title: {title}, Text length: {len(text)},\nexcerpt: {text}.")
                if self.debug:
                    screenshot_dir: Path = Path("logs/screenshots")
                    screenshot_dir.mkdir(exist_ok=True)
                    screenshot_path: Path = screenshot_dir / f"screenshot-error-{NoDriverScraper.get_domain(self.url)}.jpeg"
                    await page.save_screenshot(screenshot_path)
                    self.logger.warning(f"check screenshot at [{screenshot_path}] for more details.")

            return str(text), image_urls, str(title or "")
        except Exception as e:
            self.logger.exception(f"An error occurred during scraping: {e.__class__.__name__}: {e}")
            return f"{e.__class__.__name__}: {e}", [], ""
        finally:
            try:
                if page and browser:
                    await browser.close_page(page)
                if browser:
                    await self.release_browser(browser)
            except Exception as e:
                self.logger.error(e)
