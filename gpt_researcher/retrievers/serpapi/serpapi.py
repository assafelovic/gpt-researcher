# SerpApi Retriever

from __future__ import annotations

import logging
import os
import urllib.parse

from typing import Any

# import httpx
import requests

# from langchain_core.callbacks import CallbackManagerForRetrieverRun
# from langchain_core.documents import Document
# from langchain_core.retrievers import BaseRetriever
from gpt_researcher.utils.logger import get_formatted_logger
from gpt_researcher.retrievers.retriever_abc import RetrieverABC

logger: logging.Logger = get_formatted_logger(__name__)


# class SerpApiSearch(BaseRetriever):
#    """SerpAPI Search Retriever that implements LangChain's BaseRetriever interface."""

#    def __init__(
#        self,
#        headers: dict[str, str] | None = None,
#    ) -> None:
#        """Initialize the SerpAPI retriever.

#        Args:
#            headers: Optional dictionary containing API keys. If not provided,
#                    will attempt to load from environment variables.
#        """
#        super().__init__()
#        self.headers: dict[str, str] = headers or {}
#        self.api_key: str = self.headers.get("serpapi_api_key") or self.get_api_key()

#    def get_api_key(self) -> str:
#        """Gets the SerpAPI key from environment variables.

#        Returns:
#            str: The SerpAPI key.

#        Raises:
#            Exception: If API key is not found in environment variables.
#        """
#        try:
#            api_key = os.environ["SERPAPI_API_KEY"]
#        except KeyError:
#            raise Exception("SerpAPI key not found. Please set the SERPAPI_API_KEY environment variable. You can get a key at https://serpapi.com/")
#        return api_key

#    def _get_relevant_documents(
#        self,
#        query: str,
#        *,
#        run_manager: CallbackManagerForRetrieverRun,
#        max_results: int = 7,
#    ) -> list[Document]:
#        """Get documents relevant to a query using SerpAPI Search.

#        Args:
#            query: The search query string.
#            run_manager: Callback manager for the retriever run.
#            max_results: Maximum number of results to return. Defaults to 7.

#        Returns:
#            List of relevant documents.
#        """
#        logger.info(f"Searching with query {query}...")

#        url = "https://serpapi.com/search.json"
#        params: dict[str, str] = {"q": query, "api_key": self.api_key}
#        encoded_url = url + "?" + urllib.parse.urlencode(params)

#        try:
#            response = requests.get(encoded_url, timeout=10)
#            response.raise_for_status()
#            search_results = response.json()
#        except Exception as e:
#            logger.exception(f"Failed fetching sources. Resulting in empty response. {e.__class__.__name__}: {e}")
#            return []

#        if not search_results or "organic_results" not in search_results:
#            return []

#        documents: list[Document] = []
#        results_processed = 0

# Convert search results to Document objects
#        for result in search_results["organic_results"]:
# Skip YouTube results
#            if "youtube.com" in result["link"]:
#                continue

#            if results_processed >= max_results:
#                break

# Create Document object with metadata
#            doc = Document(
#                page_content=result["snippet"],
#                metadata={
#                    "title": result["title"],
#                    "source": result["link"],
#                },
#            )
#            documents.append(doc)
#            results_processed += 1

#        return documents

#    async def _aget_relevant_documents(
#        self,
#        query: str,
#        *,
#        run_manager: CallbackManagerForRetrieverRun,
#        max_results: int = 7,
#    ) -> list[Document]:
#        """Asynchronously get documents relevant to a query using SerpAPI Search.

#        Args:
#            query: The search query string.
#            run_manager: Callback manager for the retriever run.
#            max_results: Maximum number of results to return. Defaults to 7.

#        Returns:
#            List of relevant documents.
#        """
#        logger.info(f"Searching with query {query}...")

#        url = "https://serpapi.com/search.json"
#        params: dict[str, str] = {"q": query, "api_key": self.api_key}

#        try:
#            async with httpx.AsyncClient() as client:
#                response = await client.get(url, params=params, timeout=10.0)
#                response.raise_for_status()
#                search_results = response.json()
#        except Exception as e:
#            logger.exception(f"Failed fetching sources. Resulting in empty response. {e.__class__.__name__}: {e}")
#            return []

#        if not search_results or "organic_results" not in search_results:
#            return []

#        documents: list[Document] = []
#        results_processed = 0

# Convert search results to Document objects
#        for result in search_results["organic_results"]:
# Skip YouTube results
#            if "youtube.com" in result["link"]:
#                continue

#            if results_processed >= max_results:
#                break

# Create Document object with metadata
#            doc = Document(
#                page_content=result["snippet"],
#                metadata={
#                    "title": result["title"],
#                    "source": result["link"],
#                },
#            )
#            documents.append(doc)
#            results_processed += 1

#        return documents
# =======


class SerpApiSearch(RetrieverABC):
    """SerpApi Retriever."""

    def __init__(
        self,
        query: str,
        query_domains: list[str] | None = None,
        *args: Any,  # provided for compatibility with other scrapers
        **kwargs: Any,  # provided for compatibility with other scrapers
    ) -> None:
        """
        Initializes the SerpApiSearch object
        Args:
            query: The search query string.
            query_domains: The domains to whitelist for search.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.query: str = query
        self.query_domains: list[str] | None = query_domains
        self.api_key: str = self.get_api_key()
        self.args: tuple[Any, ...] = args
        self.kwargs: dict[str, Any] = kwargs

    def get_api_key(self) -> str:
        """Gets the SerpApi API key.

        Returns:
            str: The SerpApi API key.

        Raises:
            KeyError: If the SerpApi API key is not found in the environment variables.
        """
        try:
            api_key: str = os.environ["SERPAPI_API_KEY"]
        except KeyError:
            raise KeyError("SerpApi API key not found. Please set the SERPAPI_API_KEY environment variable. You can get a key at https://serpapi.com/")
        return api_key

    def search(
        self,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """Searches the query.

        Useful for general internet search queries using SerpApi.

        Returns:
            List of dictionaries containing title, href, and body of each paper.
        """
        # If max_results is the default, check environment variable
        if max_results is None:  # Default value
            max_results = int(os.environ.get("MAX_SOURCES", 10))

        logging.info(f"SerpApiSearch: Searching with query {self.query}...")
        url: str = "https://serpapi.com/search.json"

        search_query: str = self.query
        if self.query_domains:
            # Add site:domain1 OR site:domain2 OR ... to the search query
            search_query += " site:" + " OR site:".join(self.query_domains)

        params: dict[str, str] = {
            "q": search_query,
            "api_key": self.api_key,
        }
        encoded_url: str = url + "?" + urllib.parse.urlencode(params)
        search_response: list[dict[str, str]] = []
        try:
            response: requests.Response = requests.get(encoded_url, timeout=10)
            if response.status_code == 200:
                search_results: dict[str, Any] = response.json()
                if search_results:
                    results: list[dict[str, Any]] = search_results["organic_results"]
                    results_processed: int = 0
                    for result in results:
                        # skip youtube results
                        if "youtube.com" in result["link"]:
                            continue
                        if results_processed >= max_results:
                            break
                        search_result: dict[str, str] = {
                            "title": result["title"],
                            "href": result["link"],
                            "body": result["snippet"],
                        }
                        search_response.append(search_result)
                        results_processed += 1
        except Exception as e:
            logger.exception(f"Error: {e.__class__.__name__}: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []

        return search_response
