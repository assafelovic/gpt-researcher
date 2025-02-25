from bs4 import BeautifulSoup
import os
from ..utils import get_relevant_images

class FireCrawl:

    def __init__(self, link, session=None):
        self.link = link
        self.session = session
        from firecrawl import FirecrawlApp
        self.firecrawl = FirecrawlApp(api_key=self.get_api_key(), api_url=self.get_server_url())

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
            response = self.firecrawl.scrape_url(url=self.link, params={"formats": ["markdown"]})

            # Check if the page has been scraped success
            if "error" in response:
                print("Scrape failed! : " + str(response["error"]))
                return "", [], ""
            elif response["metadata"]["statusCode"] != 200:
                print("Scrape failed! : " + str(response))
                return "", [], ""

            # Extract the content (markdown) and title from FireCrawl response
            content = response["markdown"]
            title = response["metadata"]["title"]

            # Parse the HTML content of the response to create a BeautifulSoup object for the utility functions
            response_bs = self.session.get(self.link, timeout=4)
            soup = BeautifulSoup(
                response_bs.content, "lxml", from_encoding=response_bs.encoding
            )

            # Get relevant images using the utility function
            image_urls = get_relevant_images(soup, self.link)

            return content, image_urls, title

        except Exception as e:
            print("Error! : " + str(e))
            return "", [], ""