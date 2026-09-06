"""Sofya search retriever for GPT Researcher.

Sofya is a web search API that returns the content of the result pages, not
only the links and snippets. Set SOFYA_API_KEY in your environment. Get a key
at https://sofya.co
"""

import logging
import os

import requests

# Depths the Sofya search API accepts. "basic" also returns the text of each
# result page; "snippets" returns links and short snippets only.
SEARCH_DEPTHS = ("basic", "snippets")
DEFAULT_SEARCH_DEPTH = "basic"
DEFAULT_MAX_RESULTS = 10
# The API rejects a larger count.
MAX_RESULTS_LIMIT = 20


def _as_text(value) -> str:
    """Return a string for a field that should be text but may not be."""
    if isinstance(value, str):
        return value
    if value is None or isinstance(value, (dict, list)):
        return ""
    return str(value)


class SofyaSearch:
    """
    Sofya API Retriever
    """

    def __init__(self, query, headers=None, topic="general", query_domains=None):
        """
        Initializes the SofyaSearch object.

        Args:
            query (str): The search query string.
            headers (dict, optional): Additional headers to include in the request. Defaults to None.
            topic (str, optional): The topic for the search. Defaults to "general".
            query_domains (list, optional): List of domains to include in the search. Defaults to None.
        """
        input_headers = headers or {}
        self.query = query
        self.topic = topic
        self.base_url = "https://sofya.co/v1/search"
        self.logger = logging.getLogger(__name__)
        self.api_key = self.get_api_key(input_headers)
        self.search_depth = self.get_search_depth(input_headers)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.query_domains = query_domains or None

    @property
    def requires_scraping(self) -> bool:
        """At "basic" depth the results already carry the page text."""
        return self.search_depth != "basic"

    def get_api_key(self, headers):
        """
        Gets the Sofya API key
        Args:
            headers (dict): The headers passed to the retriever.
        Returns:

        """
        api_key = headers.get("sofya_api_key")
        if not api_key:
            try:
                api_key = os.environ["SOFYA_API_KEY"]
            except KeyError:
                raise Exception(
                    "Sofya API key not found. Please set the SOFYA_API_KEY "
                    "environment variable. Get a key at https://sofya.co"
                )
        return api_key

    def get_search_depth(self, headers):
        """
        Gets the search depth, defaulting to "basic".

        An unknown value is not sent to the API. It is logged and the default
        is used instead.
        Args:
            headers (dict): The headers passed to the retriever.
        Returns:
            One of SEARCH_DEPTHS.
        """
        depth = headers.get("sofya_search_depth") or os.environ.get(
            "SOFYA_SEARCH_DEPTH"
        )
        if not depth:
            return DEFAULT_SEARCH_DEPTH
        depth = _as_text(depth).strip().lower()
        if depth not in SEARCH_DEPTHS:
            self.logger.warning(
                "Unknown Sofya search depth %r, using %r. Valid values: %s.",
                depth,
                DEFAULT_SEARCH_DEPTH,
                ", ".join(SEARCH_DEPTHS),
            )
            return DEFAULT_SEARCH_DEPTH
        return depth

    def _get_max_results(self, max_results):
        """Clamps the requested result count to what the API accepts."""
        try:
            max_results = int(max_results)
        except (TypeError, ValueError):
            self.logger.warning(
                "Invalid Sofya max results %r, using %d.",
                max_results,
                DEFAULT_MAX_RESULTS,
            )
            max_results = DEFAULT_MAX_RESULTS
        return max(1, min(max_results, MAX_RESULTS_LIMIT))

    def _get_include_domains(self):
        """Returns the domains to restrict the search to, at most ten."""
        domains = []
        for domain in self.query_domains or []:
            domain = _as_text(domain).strip()
            # The API takes plain host names, so drop any scheme or path.
            domain = domain.split("://")[-1].split("/")[0]
            if domain and domain not in domains:
                domains.append(domain)
        return domains[:10]

    def search(self, max_results=10):
        """
        Searches the query
        Returns:

        """
        count = self._get_max_results(max_results)
        payload = {
            "query": self.query,
            "search_depth": self.search_depth,
            "max_results": count,
            "topic": self.topic,
        }
        include_domains = self._get_include_domains()
        if include_domains:
            payload["include_domains"] = include_domains

        try:
            response = requests.post(
                self.base_url, headers=self.headers, json=payload, timeout=60
            )
            # Raises an HTTPError if the request returned an unsuccessful status code
            response.raise_for_status()
            results = response.json()
        except Exception as e:
            self.logger.error(
                f"Error fetching Sofya search results: {e}. Resulting in empty response."
            )
            return []

        if not isinstance(results, dict):
            return []
        sources = results.get("results") or []
        if not isinstance(sources, list):
            return []

        # Normalize the results to match the format of the other search APIs.
        # Skip rows that are not dicts or have no URL, and default the rest to
        # "" so one odd row does not drop the whole page of results.
        search_results = []
        for source in sources:
            if not isinstance(source, dict):
                continue
            href = _as_text(source.get("url")).strip()
            if not href:
                continue
            content = _as_text(source.get("content"))
            description = _as_text(source.get("description"))
            search_result = {
                "title": _as_text(source.get("title")),
                "href": href,
                "body": description or content,
            }
            # At "basic" depth the page text is already here, so pass it on as
            # raw_content and let GPT Researcher skip scraping this URL.
            if not self.requires_scraping and content:
                search_result["raw_content"] = content
            search_results.append(search_result)

        return search_results
