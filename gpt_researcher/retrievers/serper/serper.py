from __future__ import annotations

import json
import os
from typing import Any
import requests

from gpt_researcher.retrievers.retriever_abc import RetrieverABC


class SerperSearch(RetrieverABC):
    """
    Google Serper Retriever with support for domain, country, language, and time filtering.
    """

    def __init__(
        self,
        query: str,
        query_domains: list[str] | None = None,
        country: str | None = None,
        language: str | None = None,
        time_range: str | None = None,
        exclude_sites: list[str] | None = None,
    ):
        """
        Initializes the SerperSearch object.

        Args:
            query (str): The search query string.
            query_domains (list[str], optional): List of domains to include in the search.
            country (str, optional): Country code for search results (e.g., 'us', 'kr', 'jp').
            language (str, optional): Language code for search results (e.g., 'en', 'ko', 'ja').
            time_range (str, optional): Time range filter (e.g., 'qdr:h', 'qdr:d', 'qdr:w', 'qdr:m', 'qdr:y').
            exclude_sites (list[str], optional): List of sites to exclude from search results.
        """
        self.query: str = query
        self.query_domains: list[str] | None = query_domains or None
        self.country: str | None = country or os.getenv("SERPER_REGION")
        self.language: str | None = language or os.getenv("SERPER_LANGUAGE")
        self.time_range: str | None = time_range or os.getenv("SERPER_TIME_RANGE")
        self.exclude_sites: list[str] = exclude_sites or self._get_exclude_sites_from_env()
        self.api_key: str = self.get_api_key()

    def _get_exclude_sites_from_env(self) -> list[str]:
        """
        Gets the list of sites to exclude from environment variables.
        Returns:
            list[str]: List of sites to exclude.
        """
        exclude_sites_env = os.getenv("SERPER_EXCLUDE_SITES", "")
        if exclude_sites_env:
            return [site.strip() for site in exclude_sites_env.split(",") if site.strip()]
        return []

    def get_api_key(self) -> str:
        """
        Gets the Serper API key.

        Returns:
            str: The Serper API key.
        """
        api_key: str | None = os.environ.get("SERPER_API_KEY")
        if not api_key or not api_key.strip():
            raise Exception(
                "Serper API key not found. Please set the SERPER_API_KEY environment variable. "
                "You can get a key at https://serper.dev/"
            )
        return api_key


def search(
    self,
    max_results: int = 7,
) -> list[dict[str, Any]]:
    """Searches the query.

    Args:
        max_results (int, optional): The maximum number of results to return.

    Returns:
        list[dict[str, Any]]: The search results.
    """
    print(f"Searching with query {self.query}...")
    """Useful for general internet search queries using the Serp API."""

    # Search the query (see https://serper.dev/playground for the format)
    url: str = "https://google.serper.dev/search"

    # Build search parameters
    query_with_filters = self.query

    # Exclude sites using Google search syntax
    if self.exclude_sites:
        for site in self.exclude_sites:
            query_with_filters += f" -site:{site}"

    # Add domain filtering if specified
    if self.query_domains:
        # Add site:domain1 OR site:domain2 OR ... to the search query
        domain_query = " site:" + " OR site:".join(self.query_domains)
        query_with_filters += domain_query

    search_params = {
        "q": query_with_filters,
        "num": max_results
    }

    # Add optional parameters if they exist
    if self.country:
        search_params["gl"] = self.country  # Geographic location (country)

    if self.language:
        search_params["hl"] = self.language  # Host language

    if self.time_range:
        search_params["tbs"] = self.time_range  # Time-based search

    headers: dict[str, Any] = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
    data: str = json.dumps(search_params)

    resp: requests.Response = requests.request("POST", url, timeout=10, headers=headers, data=data)

    # Preprocess the results
    if resp.status_code != 200:
        raise Exception(f"Error: {resp.status_code} {resp.text}")
    try:
        search_results: dict[str, Any] = json.loads(resp.text)
    except Exception as e:
        print(f"Error: {e.__class__.__name__}: {e}. Failed fetching sources. Resulting in empty response.")
        raise Exception(f"Error: {resp.text}")

    results: list[dict[str, Any]] = search_results.get("organic", [])

    # Normalize the results to match the format of the other search APIs
    search_results_list: list[dict[str, Any]] = []
    for result in results:
        # Skip YouTube results
        if "youtube.com" in str(result.get("link", "")).casefold():
            continue
        search_result: dict[str, Any] = {
            "title": result.get("title", "No Title"),
            "href": result.get("link", "No Link"),
            "body": result.get("snippet", "No Snippet"),
        }
        search_results_list.append(search_result)

    return search_results_list

