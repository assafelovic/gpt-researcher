import os
import random
import traceback
from bs4 import BeautifulSoup
from typing import cast
import nodriver
import asyncio

from ..utils import get_relevant_images, extract_title, get_text_from_soup, clean_soup


class NoDriverScraper:
    def __init__(self, url: str, session=None):
        self.url = url
        self.session = session

    def scrape(self) -> tuple:
        return asyncio.get_event_loop().run_until_complete(self.scrape_async())

    async def scrape_async(self) -> tuple:
        if not self.url:
            print("URL not specified")
            return (
                "A URL was not specified, cancelling request to browse website.",
                [],
                "",
            )

        browser = await nodriver.start(headless=False)
        try:
            page = await browser.get(self.url)
            await page.wait()
            await page.sleep(random.random() + 3)
            await page.wait()

            async def scroll_to_bottom():
                total_scroll_percent = 0
                max_scroll_percent = 10000  # 100 pages
                while True:
                    scroll_percent = random.randrange(50, 100)
                    total_scroll_percent += scroll_percent
                    await page.bring_to_front()
                    await page.scroll_down(scroll_percent)
                    await page.wait()
                    await page.sleep(random.random() * 0.5)

                    if total_scroll_percent >= max_scroll_percent:
                        break

                    if cast(
                        float,
                        await page.evaluate("window.innerHeight + window.scrollY"),
                    ) >= cast(
                        float,
                        await page.evaluate("document.scrollingElement.scrollHeight"),
                    ):
                        break

            await scroll_to_bottom()
            html = await page.get_content()
            await page.close()
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
            if browser:
                browser.stop()
