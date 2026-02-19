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

        response = requests.post(url, headers=headers, json=data)

        json_response = response.json()
        results = json_response["data"]["webPages"]["value"]
        search_results = []

        # Normalize the results to match the format of the other search APIs
        for result in results:
            search_result = {
                "title": result["name"],
                "href": result["url"],
                "body": result["snippet"],
            }
            search_results.append(search_result)

        return search_results