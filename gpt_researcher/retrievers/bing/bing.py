from __future__ import annotations

import json
import logging
import os

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
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize the BingSearch retriever.

        Args:
            headers: Optional dictionary containing API keys. If not provided,
                    will attempt to load from environment variables.
        """
        super().__init__()
        self.headers: dict[str, str] = headers or {}
        self.api_key: str = self.headers.get("bing_api_key") or self.get_api_key()

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

        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json",
        }
        params = {
            "responseFilter": "Webpages",
            "q": query,
            "count": max_results,
            "setLang": "en-GB",
            "textDecorations": False,
            "textFormat": "HTML",
            "safeSearch": "Strict",
        }

        resp = requests.get(url, headers=headers, params=params)

        if resp.status_code < 200 or resp.status_code >= 300:
            logger.warning("Bing search: unexpected response status: ", resp.status_code)
            return []

        try:
            search_results = json.loads(resp.text)
            results = search_results["webPages"]["value"]
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

        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json",
        }
        params = {
            "responseFilter": "Webpages",
            "q": query,
            "count": max_results,
            "setLang": "en-GB",
            "textDecorations": False,
            "textFormat": "HTML",
            "safeSearch": "Strict",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params=params)

        if resp.status_code < 200 or resp.status_code >= 300:
            logger.warning("Bing search: unexpected response status: ", resp.status_code)
            return []

        try:
            search_results = resp.json()
            results = search_results["webPages"]["value"]
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
