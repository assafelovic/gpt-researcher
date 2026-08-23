from typing import Any, Dict, List
import requests
import os


class CustomRetriever:
    """
    Custom API Retriever
    """

    def __init__(self, query: str, query_domains=None):
        self.endpoint = os.getenv('RETRIEVER_ENDPOINT')
        if not self.endpoint:
            raise ValueError("RETRIEVER_ENDPOINT environment variable not set")

        self.params = self._populate_params()
        self.query = query

    def _populate_params(self) -> Dict[str, Any]:
        """
        Populates parameters from environment variables prefixed with 'RETRIEVER_ARG_'
        """
        return {
            key[len('RETRIEVER_ARG_'):].lower(): value
            for key, value in os.environ.items()
            if key.startswith('RETRIEVER_ARG_')
        }

    def search(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Performs the search using the custom retriever endpoint.

        :param max_results: Maximum number of results to return (not currently used)
        :return: JSON response in the format:
            [
              {
                "url": "http://example.com/page1",
                "raw_content": "Content of page 1"
              },
              {
                "url": "http://example.com/page2",
                "raw_content": "Content of page 2"
              }
            ]
        """
        try:
            response = requests.get(
                self.endpoint,
                params={**self.params, "query": self.query},
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as e:
            # ValueError covers JSONDecodeError (subclass) and other parse fails.
            print(f"Failed to retrieve search results: {e}")
            return []

        # Contract: callers iterate the return value. A null JSON body or a
        # non-list payload used to surface as TypeError later (or as the
        # documented but surprising Optional). Always hand back a list.
        if payload is None:
            return []
        if not isinstance(payload, list):
            print(
                "Custom retriever response must be a JSON list of "
                "{url, raw_content} objects; got "
                f"{type(payload).__name__}"
            )
            return []

        # Contract is list[{url, raw_content}]. Downstream reads .get on
        # each item; filter non-dicts and rows without a usable URL so a
        # single malformed edge cannot crash the research pipeline.
        cleaned: List[Dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            url = item.get("url") or item.get("href") or ""
            if not url:
                continue
            cleaned.append(
                {
                    "url": url,
                    "raw_content": item.get("raw_content") or item.get("body") or "",
                }
            )
        return cleaned
