# BoCha Search Retriever

# libraries
import os
import requests
import json
import logging


class BoChaSearch():
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
        self.api_key = os.environ["BOCHA_API_KEY"]

    def search(self, max_results=7) -> list[dict[str]]:
        """
        Searches the query
        Returns:

        """
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

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            json_response = response.json()
        except Exception as e:
            logging.getLogger(__name__).error(
                "BoCha search request failed: %s. Returning empty results.", e
            )
            return []

        data_block = json_response.get("data") if isinstance(json_response, dict) else None
        web_pages = data_block.get("webPages") if isinstance(data_block, dict) else None
        results = web_pages.get("value") if isinstance(web_pages, dict) else None
        if not isinstance(results, list):
            logging.getLogger(__name__).warning(
                "BoCha search returned unexpected payload shape. Returning empty results."
            )
            return []

        search_results = []
        # Normalize the results to match the format of the other search APIs
        for result in results:
            if not isinstance(result, dict):
                continue
            url = result.get("url")
            if not url:
                continue
            search_results.append(
                {
                    "title": result.get("name") or "",
                    "href": url,
                    "body": result.get("snippet") or "",
                }
            )

        return search_results