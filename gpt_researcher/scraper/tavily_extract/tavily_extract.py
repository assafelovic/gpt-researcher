from bs4 import BeautifulSoup
import os
from ..utils import get_relevant_images, extract_title

class TavilyExtract:

    def __init__(self, link, session=None):
        self.link = link
        self.session = session
        from tavily import TavilyClient
        self.tavily_client = TavilyClient(api_key=self.get_api_key())

    def get_api_key(self) -> str:
        """
        Gets the Tavily API key
        Returns:
        Api key (str)
        """
        try:
            api_key = os.environ["TAVILY_API_KEY"]
        except KeyError:
            raise Exception(
                "Tavily API key not found. Please set the TAVILY_API_KEY environment variable.")
        return api_key

    def scrape(self) -> tuple:
        """
        This function extracts content from a specified link using the Tavily Python SDK, the title and
        images from the link are extracted using the functions from `gpt_researcher/scraper/utils.py`.

        Returns:
          The `scrape` method returns a tuple containing the extracted content, a list of image URLs, and
        the title of the webpage specified by the `self.link` attribute. It uses the Tavily Python SDK to
        extract and clean content from the webpage. If any exception occurs during the process, an error
        message is printed and an empty result is returned.
        """

        try:
            response = self.tavily_client.extract(urls=self.link)
            if not isinstance(response, dict):
                return "", [], ""
            if response.get("failed_results"):
                return "", [], ""

            results = response.get("results") or []
            if not isinstance(results, list) or not results:
                return "", [], ""
            first = results[0]
            if not isinstance(first, dict):
                return "", [], ""
            content = first.get("raw_content") or ""

            # Image/title enrichment is best-effort. Callers often construct
            # TavilyExtract(link, session=None); a bare session.get would
            # TypeError and (with the broad except) previously discarded the
            # already-extracted Tavily content too. Keep content even when
            # enrichment is unavailable.
            image_urls = []
            title = ""
            if self.session is not None:
                try:
                    response_bs = self.session.get(self.link, timeout=4)
                    soup = BeautifulSoup(
                        response_bs.content,
                        "lxml",
                        from_encoding=response_bs.encoding,
                    )
                    image_urls = get_relevant_images(soup, self.link)
                    title = extract_title(soup)
                except Exception as enrich_err:
                    print(
                        "Warning: TavilyExtract image/title enrichment failed: "
                        + str(enrich_err)
                    )

            return content, image_urls, title

        except Exception as e:
            print("Error! : " + str(e))
            return "", [], ""
