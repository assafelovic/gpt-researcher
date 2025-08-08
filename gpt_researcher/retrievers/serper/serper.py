# Google Serper Retriever

# libraries
import os
import requests
import json


class SerperSearch():
    """
    Google Serper Retriever with support for country, language, and date filtering
    """
    def __init__(self, query, query_domains=None, country=None, language=None, time_range=None, exclude_sites=None):
        """
        Initializes the SerperSearch object
        Args:
            query (str): The search query string.
            query_domains (list, optional): List of domains to include in the search. Defaults to None.
            country (str, optional): Country code for search results (e.g., 'us', 'kr', 'jp'). Defaults to None.
            language (str, optional): Language code for search results (e.g., 'en', 'ko', 'ja'). Defaults to None.
            time_range (str, optional): Time range filter (e.g., 'qdr:h', 'qdr:d', 'qdr:w', 'qdr:m', 'qdr:y'). Defaults to None.
            exclude_sites (list, optional): List of sites to exclude from search results. Defaults to None.
        """
        self.query = query
        self.query_domains = query_domains or None
        self.country = country or os.getenv("SERPER_REGION")
        self.language = language or os.getenv("SERPER_LANGUAGE")
        self.time_range = time_range or os.getenv("SERPER_TIME_RANGE")
        self.exclude_sites = exclude_sites or self._get_exclude_sites_from_env()
        self.api_key = self.get_api_key()

    def _get_exclude_sites_from_env(self):
        """
        Gets the list of sites to exclude from environment variables
        Returns:
            list: List of sites to exclude
        """
        exclude_sites_env = os.getenv("SERPER_EXCLUDE_SITES", "")
        if exclude_sites_env:
            # Split by comma and strip whitespace
            return [site.strip() for site in exclude_sites_env.split(",") if site.strip()]
        return []

    def get_api_key(self):
        """
        Gets the Serper API key
        Returns:

        """
        try:
            api_key = os.environ["SERPER_API_KEY"]
        except:
            raise Exception("Serper API key not found. Please set the SERPER_API_KEY environment variable. "
                            "You can get a key at https://serper.dev/")
        return api_key

    def search(self, max_results=7):
        """
        Searches the query with optional country, language, and time filtering
        Returns:
            list: List of search results with title, href, and body
        """
        print("Searching with query {0}...".format(self.query))
        """Useful for general internet search queries using the Serper API."""

        # Search the query (see https://serper.dev/playground for the format)
        url = "https://google.serper.dev/search"

        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

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

        data = json.dumps(search_params)

        resp = requests.request("POST", url, timeout=10, headers=headers, data=data)

        # Preprocess the results
        if resp is None:
            return
        try:
            search_results = json.loads(resp.text)
        except Exception:
            return
        if search_results is None:
            return

        results = search_results.get("organic", [])
        search_results = []

        # Normalize the results to match the format of the other search APIs
        # Excluded sites should already be filtered out by the query parameters
        for result in results:
            search_result = {
                "title": result["title"],
                "href": result["link"],
                "body": result["snippet"],
            }
            search_results.append(search_result)

        return search_results
