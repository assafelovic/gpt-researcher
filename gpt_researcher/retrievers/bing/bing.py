from __future__ import annotations

import json
import logging

# Bing Search Retriever
# libraries
import os

from typing import Any

import httpx
import requests

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

logger = logging.getLogger(__name__)


class BingSearch(BaseRetriever):
    """Bing Search Retriever that implements LangChain's BaseRetriever interface."""

    def __init__(
        self,
        query: str,
        query_domains: list[str] | None = None,
    ):
        """Initialize the BingSearch retriever.

        Args:
            headers: Optional dictionary containing API keys. If not provided,
                    will attempt to load from environment variables.
        """
        super().__init__()
        self.query: str = query
        self.query_domains: list[str] | None = query_domains or None
        self.api_key: str = self.get_api_key()
        self.logger: logging.Logger = logging.getLogger(__name__)

    def search(
        self,
        max_results: int = 7,
    ) -> list[dict[str, Any]]:
        """
        Searches the query
        Returns:
            list[dict[str, Any]]: A list of dictionaries containing the search results.
        """
        print("Searching with query {0}...".format(self.query))
        """Useful for general internet search queries using the Bing API."""

        # Search the query
        url = "https://api.bing.microsoft.com/v7.0/search"

        headers: dict[str, str] = {"Ocp-Apim-Subscription-Key": self.api_key, "Content-Type": "application/json"}
        # TODO: Add support for query domains
        params: dict[str, Any] = {
            "count": max_results,
            "q": self.query,
            "responseFilter": "Webpages",
            "safeSearch": "Strict",
            "setLang": "en-GB",
            "textDecorations": False,
            "textFormat": "HTML",
        }

        resp: requests.Response = requests.get(url, headers=headers, params=params)

        # Preprocess the results
        if resp is None:
            return []
        try:
            search_results: dict[str, Any] = json.loads(resp.text)
            results: list[dict[str, Any]] = search_results["webPages"]["value"]
        except Exception as e:
            self.logger.error(f"Error parsing Bing search results: {e}. Resulting in empty response.")
            return []
        if search_results is None:
            self.logger.warning(f"No search results found for query: {self.query}")
            return []
        search_results_list: list[dict[str, Any]] = []

        # Normalize the results to match the format of the other search APIs
        for result in results:
            # skip youtube results
            if "youtube.com" in result["url"]:
                continue
            search_result: dict[str, Any] = {
                "title": result["name"],
                "href": result["url"],
                "body": result["snippet"],
            }
            search_results_list.append(search_result)

        return search_results_list


    def get_api_key(self) -> str:
        """Gets the Bing API key from environment variables.

        Returns:
            str: The Bing API key.

        Raises:
            Exception: If API key is not found in environment variables.
        """
        try:
            api_key = os.environ["BING_API_KEY"]
        except KeyError:
            raise Exception("Bing API key not found. Please set the BING_API_KEY environment variable.")
        return api_key

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        max_results: int = 7,
    ) -> list[Document]:
        """Get documents relevant to a query using Bing Search API.

        Args:
            query: The search query string.
            run_manager: Callback manager for the retriever run.
            max_results: Maximum number of results to return. Defaults to 7.

        Returns:
            List of relevant documents.
        """
        logger.info(f"Searching with query {query}...")

        url: str = "https://api.bing.microsoft.com/v7.0/search"
        headers: dict[str, str] = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json",
        }
        params: dict[str, Any] = {
            "responseFilter": "Webpages",
            "q": query,
            "count": max_results,
            "setLang": "en-GB",
            "textDecorations": False,
            "textFormat": "HTML",
            "safeSearch": "Strict",
        }

        resp: requests.Response = requests.get(url, headers=headers, params=params)

        if resp.status_code < 200 or resp.status_code >= 300:
            logger.warning("Bing search: unexpected response status: ", resp.status_code)
            return []

        try:
            search_results: dict[str, Any] = json.loads(resp.text)
            results: list[dict[str, Any]] = search_results["webPages"]["value"]
        except Exception as e:
            logger.exception(f"Error parsing Bing search results: {e}. Resulting in empty response.")
            return []

        if not results:
            logger.warning(f"No search results found for query: {query}")
            return []

        documents: list[Document] = []

        # Convert search results to Document objects
        for result in results:
            # Skip YouTube results
            if "youtube.com" in result["url"]:
                continue

            # Create Document object with metadata
            doc = Document(
                page_content=result["snippet"],
                metadata={
                    "title": result["name"],
                    "source": result["url"],
                },
            )
            documents.append(doc)

        return documents[:max_results]

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        max_results: int = 7,
    ) -> list[Document]:
        """Asynchronously get documents relevant to a query.

        This implementation uses async HTTP calls for better performance.
        """
        logger.info(f"Searching with query {query}...")

        url: str = "https://api.bing.microsoft.com/v7.0/search"
        headers: dict[str, str] = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json",
        }
        params: dict[str, Any] = {
            "responseFilter": "Webpages",
            "q": query,
            "count": max_results,
            "setLang": "en-GB",
            "textDecorations": False,
            "textFormat": "HTML",
            "safeSearch": "Strict",
        }

        async with httpx.AsyncClient() as client:
            resp: httpx.Response = await client.get(url, headers=headers, params=params)

        if resp.status_code < 200 or resp.status_code >= 300:
            logger.warning("Bing search: unexpected response status: ", resp.status_code)
            return []

        try:
            search_results: dict[str, Any] = resp.json()
            results: list[dict[str, Any]] = search_results["webPages"]["value"]
        except Exception as e:
            logger.exception(f"Error parsing Bing search results: {e}. Resulting in empty response.")
            return []

        if not results:
            logger.warning(f"No search results found for query: {query}")
            return []

        documents: list[Document] = []

        # Convert search results to Document objects
        for result in results:
            # Skip YouTube results
            if "youtube.com" in result["url"]:
                continue

            # Create Document object with metadata
            doc = Document(
                page_content=result["snippet"],
                metadata={
                    "title": result["name"],
                    "source": result["url"],
                },
            )
            documents.append(doc)

        return documents[:max_results]
