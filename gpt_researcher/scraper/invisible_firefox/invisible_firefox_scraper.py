import os

from bs4 import BeautifulSoup

from ..utils import get_relevant_images, extract_title, get_text_from_soup, clean_soup


class InvisibleFirefoxScraper:
    """Opt-in scraper that renders a page with a patched, fingerprint-real Firefox
    (``invisible_playwright``) before parsing it, for sources that block or fingerprint
    stock automation. Once the HTML is rendered it is parsed with the same BeautifulSoup
    utilities the other scrapers use, so the output format is unchanged.

    Select it with ``SCRAPER=invisible_firefox``; when it is not selected nothing changes,
    so defaults are untouched. ``invisible_playwright`` is imported lazily and is therefore
    NOT a required dependency: install it only if you use this scraper::

        pip install "git+https://github.com/feder-cr/invisible_playwright.git"
        python -m invisible_playwright fetch   # download the patched browser once

    Optional env: ``INVISIBLE_FIREFOX_SEED`` pins the fingerprint (stable identity across runs).
    """

    def __init__(self, link, session=None):
        self.link = link
        self.session = session

    async def scrape_async(self):
        try:
            try:
                from invisible_playwright.async_api import InvisiblePlaywright
            except ImportError as e:
                raise ImportError(
                    "InvisibleFirefoxScraper requires invisible_playwright. Install it with "
                    '`pip install "git+https://github.com/feder-cr/invisible_playwright.git"` '
                    "and run `python -m invisible_playwright fetch` to download the browser."
                ) from e

            raw_seed = os.environ.get("INVISIBLE_FIREFOX_SEED")
            kwargs = {"headless": True}
            if raw_seed:
                kwargs["seed"] = int(raw_seed, 0)

            async with InvisiblePlaywright(**kwargs) as browser:
                ctx = await browser.new_context()
                page = await ctx.new_page()
                await page.goto(self.link, wait_until="domcontentloaded", timeout=30000)
                html = await page.content()

            soup = clean_soup(BeautifulSoup(html, "lxml"))
            content = get_text_from_soup(soup)
            image_urls = get_relevant_images(soup, self.link)
            title = extract_title(soup)
            return content, image_urls, title

        except Exception as e:
            print("Error! : " + str(e))
            return "", [], ""
