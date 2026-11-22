# BoCha Search Retriever

# libraries
import logging
import os
import requests


class BoChaSearch:
    """
    BoCha Search Retriever
    """

    def __init__(self, query, query_domains=None):
        """
        Initializes the BoChaSearch object
        Args:
            query:
        """
        self.query = query
        self.query_domains = query_domains or None
        self.api_key = self.get_api_key()

    def get_api_key(self):
        """
        Gets the BoCha API key
        Returns:

        """
        try:
            api_key = os.environ["BOCHA_API_KEY"]
        except KeyError:
            raise Exception(
                "BoCha API key not found. Please set the BOCHA_API_KEY environment variable. "
                "Get a key at https://api.bochaai.com"
            )
        return api_key

    def search(self, max_results=7) -> list[dict[str]]:
        """
        Searches the query
        Returns:

        """
        if max_results <= 0:
            return []

        url = 'https://api.bochaai.com/v1/web-search'
        headers = {
            'Authorization': f'Bearer {self.api_key}',  # 请替换为你的API密钥
            'Content-Type': 'application/json'
        }
        data = {
            "query": self.query,
            "freshness": "noLimit",  # 搜索的时间范围，
            "summary": True,  # 是否返回长文本摘要
            "count": max_results
        }
        if self.query_domains and len(self.query_domains) > 0:
            clean_domains = [
                d.strip()
                for d in self.query_domains
                if isinstance(d, str) and d.strip()
            ]
            if clean_domains:
                data["include"] = "|".join(clean_domains)

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            json_response = response.json()
        except (requests.RequestException, ValueError) as e:
            logging.getLogger(__name__).warning(
                f"Error: {e}. Failed fetching sources. Resulting in empty response."
            )
            return []

        # The BoCha response shape is data.webPages.value; any of these may be
        # missing on an error/empty payload, so walk it defensively rather than
        # KeyError-ing the whole research run.
        results = (
            ((json_response or {}).get("data") or {}).get("webPages") or {}
        ).get("value") or []
        if not isinstance(results, list):
            return []

        search_results = []

        # Normalize the results to match the format of the other search APIs.
        # Skip non-dict rows / empty URLs; default missing fields to "".
        for result in results:
            if not isinstance(result, dict):
                continue
            href = result.get("url") or ""
            if not href:
                continue
            search_results.append(
                {
                    "title": result.get("name") or "",
                    "href": href,
                    "body": result.get("snippet") or "",
                }
            )
            if len(search_results) >= max_results:
                break

        return search_results
