import requests
import json


class TavilyClient:
    def __init__(
        self, 
        api_key,
        include_domains: list = [],
        exclude_domains: list = []
    ):
        self.base_url = "https://api.tavily.com/search"
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
        }
        self.include_domains = include_domains
        self.exclude_domains = exclude_domains

    def _search(self, query, search_depth="basic", topic="general", days=2, max_results=5,
                include_domains=None, exclude_domains=None,
                include_answer=False, include_raw_content=False, include_images=False,
                use_cache=True):
        """
        Internal search method to send the request to the API.
        """
        data = {
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "days": days,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "max_results": max_results,
            "include_domains": self.include_domains or None,
            "exclude_domains": self.exclude_domains or None,
            "include_images": include_images,
            "api_key": self.api_key,
            "use_cache": use_cache,
        }
        response = requests.post(self.base_url, data=json.dumps(data), headers=self.headers, timeout=100)

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()  # Raises a HTTPError if the HTTP request returned an unsuccessful status code

    def search(self, query, search_depth="basic", **kwargs):
        """
        Combined search method. Set search_depth to either "basic" or "advanced".
        """
        return self._search(query, search_depth=search_depth, **kwargs)