import random
import traceback
from bs4 import BeautifulSoup
from typing import cast
import zendriver
import asyncio

from ..utils import get_relevant_images, extract_title, get_text_from_soup, clean_soup


class NoDriverScraper:
    browser_task: asyncio.Task["Browser"] | None = None

    class Browser:
        def __init__(self, driver: zendriver.Browser):
            self.driver = driver
            self.page_count = 0
            self.has_blank_page = True

        async def get(self, url: str) -> zendriver.Tab:
            new_window = True
            if self.has_blank_page:
                new_window = False
                self.has_blank_page = False
            self.page_count += 1
            return await self.driver.get(url, new_window=new_window)

        async def close_page(self, page: zendriver.Tab):
            self.page_count -= 1
            await page.close()

    @classmethod
    async def get_browser(cls) -> Browser:

        async def create_browser():
            return cls.Browser(await zendriver.start(headless=False))

        if cls.browser_task is None:
            cls.browser_task = asyncio.create_task(create_browser())
        return await cls.browser_task

    @classmethod
    async def stop_browser_if_necessary(cls, browser: Browser):
        if browser and browser.page_count == 0:
            cls.browser_task = None
            await browser.driver.stop()

    def __init__(self, url: str, session=None):
        self.url = url
        self.session = session

    async def scrape_async(self) -> tuple:
        if not self.url:
            print("URL not specified")
            return (
                "A URL was not specified, cancelling request to browse website.",
                [],
                "",
            )

        browser: NoDriverScraper.Browser | None = None
        page: zendriver.Tab | None = None
        try:
            browser = await self.get_browser()
            page = await browser.get(self.url)
            await page.wait()
            await page.sleep(random.uniform(2.5, 3.3))
            await page.wait()

            async def scroll_to_bottom():
                total_scroll_percent = 0
                max_scroll_percent = 10000  # 100 pages
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
