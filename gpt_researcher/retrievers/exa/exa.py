from __future__ import annotations

import logging
import os

from typing import TYPE_CHECKING, Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from gpt_researcher.utils import check_pkg

if TYPE_CHECKING:
    from exa_py import Exa
    from exa_py.api import ResultWithText, SearchResponse

logger = logging.getLogger(__name__)


class ExaSearch(BaseRetriever):
    """Exa Search Retriever that implements LangChain's BaseRetriever interface."""

    def __init__(
        self,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize the Exa retriever.

        Args:
            headers: Optional dictionary containing API keys. If not provided,
                    will attempt to load from environment variables.

        Raises:
            ImportError: If exa_py package is not installed.
        """
        super().__init__()
        self.headers: dict[str, str] = headers or {}

        # This validation is necessary since exa_py is optional
        check_pkg("exa_py")
        from exa_py import Exa

        self.api_key: str = self.headers.get("exa_api_key") or self._retrieve_api_key()
        self.client: Exa = Exa(api_key=self.api_key)

    def _retrieve_api_key(self) -> str:
        """Gets the Exa API key from environment variables.

        Returns:
            str: The Exa API key.

        Raises:
            Exception: If API key is not found in environment variables.
        """
        try:
            api_key = os.environ["EXA_API_KEY"]
        except KeyError:
            raise Exception("Exa API key not found. Please set the EXA_API_KEY environment variable. You can obtain your key from https://exa.ai/")
        return api_key

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        max_results: int = 10,
        use_autoprompt: bool = False,
        search_type: str = "neural",
        **filters: Any,
    ) -> list[Document]:
        """Get documents relevant to a query using Exa Search API.

        Args:
            query: The search query string.
            run_manager: Callback manager for the retriever run.
            max_results: Maximum number of results to return. Defaults to 10.
            use_autoprompt: Whether to use autoprompting. Defaults to False.
            search_type: The type of search (e.g., "neural", "keyword"). Defaults to "neural".
            **filters: Additional filters (e.g., date range, domains).

        Returns:
            List of relevant documents.
        """
        logger.info(f"Searching with query {query}...")

        try:
            results: SearchResponse = self.client.search(
                query,
                type=search_type,
                use_autoprompt=use_autoprompt,
                num_results=max_results,
                **filters,
            )
        except Exception as e:
            logger.exception(f"Failed fetching sources. Resulting in empty response. {e.__class__.__name__}: {e}")
            return []

        documents: list[Document] = []

        # Convert search results to Document objects
        for result in results.results:
            # Create Document object with metadata
            doc = Document(
                page_content=result.text,
                metadata={
                    "title": result.title if hasattr(result, "title") else "",
                    "source": result.url,
                    "body": result.text,
                    "score": result.score if hasattr(result, "score") else None,
                    "published_date": result.published_date if hasattr(result, "published_date") else None,
                },
            )
            documents.append(doc)

        return documents

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        max_results: int = 10,
        use_autoprompt: bool = False,
        search_type: str = "neural",
        **filters: Any,
    ) -> list[Document]:
        """Asynchronously get documents relevant to a query using Exa Search API.

        Note: Currently uses the synchronous implementation since exa_py doesn't provide
        async support. For better async performance, consider implementing direct async
        HTTP calls or using a different retriever.

        Args:
            query: The search query string.
            run_manager: Callback manager for the retriever run.
            max_results: Maximum number of results to return. Defaults to 10.
            use_autoprompt: Whether to use autoprompting. Defaults to False.
            search_type: The type of search (e.g., "neural", "keyword"). Defaults to "neural".
            **filters: Additional filters (e.g., date range, domains).

        Returns:
            List of relevant documents.
        """
        return self._get_relevant_documents(
            query,
            run_manager=run_manager,
            max_results=max_results,
            use_autoprompt=use_autoprompt,
            search_type=search_type,
            **filters,
        )

    def find_similar(
        self,
        url: str,
        max_results: int = 10,
        exclude_source_domain: bool = False,
        **filters: Any,
    ) -> list[Document]:
        """Find similar documents to the provided URL.

        Args:
            url: The URL to find similar documents for.
            max_results: Maximum number of results to return. Defaults to 10.
            exclude_source_domain: Whether to exclude the source domain. Defaults to False.
            **filters: Additional filters.

        Returns:
            List of similar documents.
        """
        try:
            results: SearchResponse = self.client.find_similar(
                url,
                exclude_source_domain=exclude_source_domain,
                num_results=max_results,
                **filters,
            )
        except Exception as e:
            logger.exception(f"Failed finding similar documents. {e.__class__.__name__}: {e}")
            return []

        documents: list[Document] = []

        # Convert search results to Document objects
        for result in results.results:
            doc = Document(
                page_content=result.text,
                metadata={
                    "title": result.title if hasattr(result, "title") else "",
                    "source": result.url,
                    "body": result.text,
                    "score": result.score if hasattr(result, "score") else None,
                    "published_date": result.published_date if hasattr(result, "published_date") else None,
                },
            )
            documents.append(doc)

        return documents

    def get_contents(
        self,
        ids: list[str],
        **options: Any,
    ) -> list[Document]:
        """Retrieve contents of specific documents by their IDs.

        Args:
            ids: List of document IDs to retrieve.
            **options: Additional options for content retrieval.

        Returns:
            List of documents.
        """
        try:
            results: SearchResponse[ResultWithText] = self.client.get_contents(ids, **options)
        except Exception as e:
            logger.exception(f"Failed retrieving document contents. {e.__class__.__name__}: {e}")
            return []

        documents: list[Document] = []

        # Convert results to Document objects
        for result in results.results:
            doc = Document(
                page_content=result.text,
                metadata={
                    "id": result.id,
                    "source": result.url if hasattr(result, "url") else None,
                    "body": result.text,
                },
            )
            documents.append(doc)

        return documents
