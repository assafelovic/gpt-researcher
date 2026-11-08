import os

import requests
from bs4 import BeautifulSoup

from ..utils import get_relevant_images

OUTCRAWL_SCRAPE_URL = "https://api.outcrawl.ai/v1/scrape"


class Outcrawl:
    """Scraper that reads pages through the Outcrawl scrape API (https://outcrawl.ai)."""

    def __init__(self, link, session=None):
        self.link = link
        self.session = session
        self.api_key = self.get_api_key()

    def get_api_key(self) -> str:
        """
        Gets the Outcrawl API key.

        Returns:
          Api key (str)
        """
        try:
            api_key = os.environ["OUTCRAWL_API_KEY"]
        except KeyError:
            raise Exception(
                "Outcrawl API key not found. Please set the OUTCRAWL_API_KEY environment variable."
            )
        return api_key

    def scrape(self) -> tuple:
        """
        Extracts the content and title of `self.link` with the Outcrawl scrape API, which loads the
        page in a browser and returns it as markdown. Images are extracted with the helpers in
        `gpt_researcher/scraper/utils.py`.

        Returns:
          A tuple of (content, image_urls, title). If anything goes wrong, a message is printed and
        an empty result is returned.
        """
        try:
            response = requests.post(
                OUTCRAWL_SCRAPE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"url": self.link, "formats": ["markdown"]},
                timeout=120,
            )
            if response.status_code != 200:
                print(f"Outcrawl scrape failed! Status code: {response.status_code}")
                return "", [], ""

            data = response.json()
            page_status = data.get("statusCode")
            if page_status and page_status != 200:
                print(f"Outcrawl scrape failed! Page status code: {page_status}")
                return "", [], ""

            content = data.get("markdown") or ""
            title = (data.get("metadata") or {}).get("title") or ""

            # Optional image pass. Session may be None when Outcrawl is used outside Scraper.
            image_urls = []
            if self.session is not None:
                try:
                    response_bs = self.session.get(self.link, timeout=4)
                    soup = BeautifulSoup(
                        response_bs.content,
                        "lxml",
                        from_encoding=response_bs.encoding,
                    )
                    image_urls = get_relevant_images(soup, self.link)
                except Exception as img_err:
                    print(f"Outcrawl image extraction skipped: {img_err}")

            return content, image_urls, title

        except Exception as e:
            print("Error! : " + str(e))
            return "", [], ""
