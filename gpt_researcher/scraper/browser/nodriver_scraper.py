import random
import time
import traceback
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import cast, Tuple, List, Optional
import zendriver
import asyncio

from ..utils import get_relevant_images, extract_title, get_text_from_soup, clean_soup


class NoDriverScraper:
    browser_task: Optional[asyncio.Task["NoDriverScraper.Browser"]] = None

    @staticmethod
    def get_domain(url: str) -> str:
        domain = urlparse(url).netloc
        parts = domain.split(".")
        if len(parts) > 2:
            domain = ".".join(parts[-2:])
        return domain

    class Browser:
        def __init__(self, driver: zendriver.Browser):
            self.driver = driver
            self.processing_count = 0
            self.has_blank_page = True
            self.allowed_requests_times = {}

        async def get(self, url: str) -> zendriver.Tab:
            self.processing_count += 1
            try:
                await self.rate_limit_for_domain(url)

                new_window = not self.has_blank_page
                self.has_blank_page = False
                return await self.driver.get(url, new_window=new_window)
            except Exception as e:
                self.processing_count -= 1
                raise e

        async def close_page(self, page: zendriver.Tab):
            try:
                await page.close()
            finally:
                self.processing_count -= 1

        async def rate_limit_for_domain(self, url: str) -> None:
            try:
                min_delay = 1
                domain = NoDriverScraper.get_domain(url)
                now = time.monotonic()

                # Get the next valid request time, defaulting to now
                allowed_request_time = self.allowed_requests_times.get(domain, now)

                scheduled_request_time = max(now, allowed_request_time)

                # Update the next allowed request time
                self.allowed_requests_times[domain] = (
                    scheduled_request_time + min_delay + random.uniform(0, 0.33)
                )

                sleep_time = scheduled_request_time - now
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            except Exception as e:
                # Log error but don't block the request
                print(f"Rate limiting error for {url}: {str(e)}")

    @classmethod
    async def get_browser(cls) -> "NoDriverScraper.Browser":

        async def create_browser():
            headless = True
            if headless:
                driver = await zendriver.start(headless=True, expert=True)
            else:
                driver = await zendriver.start(headless=False)
            return cls.Browser(driver)

        try:
            if cls.browser_task:
                browser = await cls.browser_task
                if not browser.driver.stopped:
                    return browser
                # Clear stopped browser
                cls.browser_task = None

            # Create new browser
            cls.browser_task = asyncio.create_task(create_browser())
            return await cls.browser_task
        except Exception as e:
            # Clear task on error
            cls.browser_task = None
            raise

    @classmethod
    async def stop_browser_if_necessary(cls, browser: Browser):
        if browser and browser.processing_count == 0:
            cls.browser_task = None
            await browser.driver.stop()

    def __init__(self, url: str, session=None):
        self.url = url
        self.session = session

    async def scrape_async(self) -> Tuple[str, List[str], str]:
        """Returns tuple of (text, image_urls, title)"""
        if not self.url:
            return (
                "A URL was not specified, cancelling request to browse website.",
                [],
                "",
            )

        browser: Optional[NoDriverScraper.Browser] = None
        page: Optional[zendriver.Tab] = None
        try:
            browser = await self.get_browser()
            page = await browser.get(self.url)
            await page.wait()
            await page.sleep(random.uniform(2.5, 3.3))
            await page.wait()

            async def scroll_to_bottom():
                total_scroll_percent = 0
                max_scroll_percent = 1500
                while True:
                    scroll_percent = random.randrange(50, 100)
                    total_scroll_percent += scroll_percent
                    await page.scroll_down(scroll_percent)
                    await page.wait()
                    await page.sleep(random.uniform(0.1, 0.5))

                    if total_scroll_percent >= max_scroll_percent:
                        break

                    if cast(
                        bool,
                        await page.evaluate(
                            "window.innerHeight + window.scrollY >= document.scrollingElement.scrollHeight"
                        ),
                    ):
                        break

            await scroll_to_bottom()
            html = await page.get_content()
            soup = BeautifulSoup(html, "lxml")
            clean_soup(soup)
            text = get_text_from_soup(soup)
            image_urls = get_relevant_images(soup, self.url)
            title = extract_title(soup)

            return text, image_urls, title
        except Exception as e:
            print(f"An error occurred during scraping: {str(e)}")
            print("Full stack trace:")
            print(traceback.format_exc())
            return (
                f"An error occurred: {str(e)}\n\nStack trace:\n{traceback.format_exc()}",
                [],
                "",
            )
        finally:
            if page and browser:
                await browser.close_page(page)
            if browser:
                await self.stop_browser_if_necessary(browser)
