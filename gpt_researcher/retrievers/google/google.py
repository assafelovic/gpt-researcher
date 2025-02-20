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


class GoogleSearch(BaseRetriever):
    """Google API Retriever that implements LangChain's BaseRetriever interface."""

    def __init__(
        self,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize the GoogleSearch retriever.

        Args:
            headers: Optional dictionary containing API keys. If not provided,
                    will attempt to load from environment variables.
        """
        super().__init__()
        self.headers: dict[str, str] = headers or {}
        self.api_key: str = self.headers.get("google_api_key") or self.get_api_key()
        self.cx_key: str = self.headers.get("google_cx_key") or self.get_cx_key()

    def get_api_key(self) -> str:
        """Gets the Google API key from environment variables.

        Returns:
            str: The Google API key.

        Raises:
            Exception: If API key is not found in environment variables.
        """
        try:
            api_key = os.environ["GOOGLE_API_KEY"]
        except KeyError:
            raise Exception(
                "Google API key not found. Please set the GOOGLE_API_KEY environment variable. You can get a key at https://developers.google.com/custom-search/v1/overview"
            )
        return api_key

    def get_cx_key(self) -> str:
        """Gets the Google CX key from environment variables.

        Returns:
            str: The Google CX key.

        Raises:
            Exception: If CX key is not found in environment variables.
        """
        try:
            api_key = os.environ["GOOGLE_CX_KEY"]
        except KeyError:
            raise Exception(
                "Google CX key not found. Please set the GOOGLE_CX_KEY environment variable. You can get a key at https://developers.google.com/custom-search/v1/overview"
            )
        return api_key

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        max_results: int = 7,
    ) -> list[Document]:
        """Get documents relevant to a query using Google Custom Search API.

        Args:
            query: The search query string.
            run_manager: Callback manager for the retriever run.
            max_results: Maximum number of results to return. Defaults to 7.

        Returns:
            List of relevant documents.
        """
        logger.info(f"Searching with query {query}...")
        url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.cx_key}&q={query}&start=1"
        resp = requests.get(url)

        if resp.status_code < 200 or resp.status_code >= 300:
            logger.warning("Google search: unexpected response status: ", resp.status_code)
            return []

        try:
            search_results = json.loads(resp.text)
        except Exception:
            return []

        if search_results is None:
            return []

        results: list[dict[str, str]] = search_results.get("items", [])
        documents: list[Document] = []

        # Convert search results to Document objects
        for result in results:
            # Skip YouTube results
            if "youtube.com" in result["link"]:
                continue

            try:
                # Create Document object with metadata
                doc = Document(
                    page_content=result["snippet"],
                    metadata={
                        "title": result["title"],
                        "source": result["link"],
                    },
                )
                documents.append(doc)
            except KeyError:
                continue

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
        url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.cx_key}&q={query}&start=1"

        async with httpx.AsyncClient() as client:
            resp = await client.get(url)

        if resp.status_code < 200 or resp.status_code >= 300:
            logger.warning("Google search: unexpected response status: ", resp.status_code)
            return []

        try:
            search_results = resp.json()
        except Exception:
            return []

        if search_results is None:
            return []

        results = search_results.get("items", [])
        documents: list[Document] = []

        # Convert search results to Document objects
        for result in results:
            # Skip YouTube results
            if "youtube.com" in result["link"]:
                continue

            try:
                # Create Document object with metadata
                doc = Document(
                    page_content=result["snippet"],
                    metadata={
                        "title": result["title"],
                        "source": result["link"],
                    },
                )
                documents.append(doc)
            except KeyError:
                continue

        return documents[:max_results]
