from __future__ import annotations

import os

from typing import TYPE_CHECKING, Any

from exa_py.api import SearchResponse
from langchain_core.documents import Document

from gpt_researcher.utils import check_pkg
from gpt_researcher.retrievers.retriever_abc import RetrieverABC

if TYPE_CHECKING:
    import logging

    from exa_py import Exa
    from exa_py.api import ResultWithText, SearchResponse, _Result

from gpt_researcher.utils.logger import get_formatted_logger

logger: logging.Logger = get_formatted_logger(__name__)


# class ExaSearch(BaseRetriever):
#    """Exa Search Retriever that implements LangChain's BaseRetriever interface."""

#    def __init__(
#        self,
#        headers: dict[str, str] | None = None,
#    ) -> None:
#        """Initialize the Exa retriever.

#        Args:
#            headers: Optional dictionary containing API keys. If not provided,
#                    will attempt to load from environment variables.

#        Raises:
#            ImportError: If exa_py package is not installed.
#        """
#        super().__init__()
#        self.headers: dict[str, str] = headers or {}

# This validation is necessary since exa_py is optional
#        check_pkg("exa_py")
#        from exa_py import Exa

#        self.api_key: str = self.headers.get("exa_api_key") or self._retrieve_api_key()
#        self.client: Exa = Exa(api_key=self.api_key)

#    def _get_relevant_documents(
#        self,
#        query: str,
#        *,
#        run_manager: CallbackManagerForRetrieverRun,
#        max_results: int = 10,
#        use_autoprompt: bool = False,
#        search_type: str = "neural",
#        **filters: Any,
#    ) -> list[Document]:
#        """Get documents relevant to a query using Exa Search API.

#        Args:
#            query: The search query string.
#            run_manager: Callback manager for the retriever run.
#            max_results: Maximum number of results to return. Defaults to 10.
#            use_autoprompt: Whether to use autoprompting. Defaults to False.
#            search_type: The type of search (e.g., "neural", "keyword"). Defaults to "neural".
#            **filters: Additional filters (e.g., date range, domains).

#        Returns:
#            List of relevant documents.
#        """
#        logger.info(f"Searching with query {query}...")

#        try:
#            results: SearchResponse = self.client.search(
#                query,
#                type=search_type,
#                use_autoprompt=use_autoprompt,
#                num_results=max_results,
#                **filters,
#            )
#        except Exception as e:
#            logger.exception(f"Failed fetching sources. Resulting in empty response. {e.__class__.__name__}: {e}")
#            return []

#        documents: list[Document] = []

# Convert search results to Document objects
#        for result in results.results:
# Create Document object with metadata
#        doc = Document(
#            page_content=result.text,
#            metadata={
#                "title": result.title if hasattr(result, "title") else "",
#                "source": result.url,
#                "body": result.text,
#                "score": result.score if hasattr(result, "score") else None,
#                "published_date": result.published_date if hasattr(result, "published_date") else None,
#                },
#            )
#        documents.append(doc)

#        return documents

#    async def _aget_relevant_documents(
#        self,
#        query: str,
#        *,
#        run_manager: CallbackManagerForRetrieverRun,
#        max_results: int = 10,
#        use_autoprompt: bool = False,
#        search_type: str = "neural",
#        **filters: Any,
#    ) -> list[Document]:
#        """Asynchronously get documents relevant to a query using Exa Search API.

#        Note: currency uses the synchronous implementation since exa_py doesn't provide
#        async support. For better async performance, consider implementing direct async
#        HTTP calls or using a different retriever.

#        Args:
#            query: The search query string.
#            run_manager: Callback manager for the retriever run.
#            max_results: Maximum number of results to return. Defaults to 10.
#            use_autoprompt: Whether to use autoprompting. Defaults to False.
#            search_type: The type of search (e.g., "neural", "keyword"). Defaults to "neural".
#            **filters: Additional filters (e.g., date range, domains).

#        Returns:
#            List of relevant documents.
#        """
#        return self._get_relevant_documents(
#            query,
#            run_manager=run_manager,
#            max_results=max_results,
#            use_autoprompt=use_autoprompt,
#            search_type=search_type,
#            **filters,
#        )


class ExaSearch(RetrieverABC):
    """Exa API Retriever."""

    def __init__(
        self,
        query: str,
        query_domains: list[str] | None = None,
        *args: Any,  # provided for compatibility with other scrapers
        **kwargs: Any,  # provided for compatibility with other scrapers
    ) -> None:
        """Initializes the ExaSearch object.

        Args:
            query: The search query.
            query_domains: The domains to search.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        # This validation is necessary since exa_py is optional
        check_pkg("exa_py")
        from exa_py import Exa

        self.query: str = query
        self.query_domains: list[str] | None = query_domains
        self.api_key: str = self._retrieve_api_key()
        self.client: Exa = Exa(api_key=self.api_key)
        self.args: tuple[Any, ...] = args
        self.kwargs: dict[str, Any] = kwargs

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
                    "body": result.text,
                    "published_date": result.published_date if hasattr(result, "published_date") else None,
                    "score": result.score if hasattr(result, "score") else None,
                    "source": result.url,
                },
            )
            documents.append(doc)

        return documents

    def get_contents(
        self,
        ids: list[str],
        **options: Any,
    ) -> list[dict[str, Any]]:
        """Retrieves the contents of the specified IDs using the Exa API.

        Args:
            ids: The IDs of the documents to retrieve.
            **options: Additional options for content retrieval.

        Returns:
            A list of document contents.
        """
        results: SearchResponse[ResultWithText] = self.client.get_contents(ids, **options)

        contents_response: list[dict[str, Any]] = [{"id": result.id, "content": result.text} for result in results.results]
        return contents_response

    def search(
        self,
        max_results: int | None = None,
        use_autoprompt: bool = False,
        search_type: str = "neural",
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Searches the query using the Exa API.

        Args:
            max_results: The maximum number of results to return.
            use_autoprompt: Whether to use autoprompting.
            search_type: The type of search (e.g., "neural", "keyword").
            **filters: Additional filters (e.g., date range, domains).

        Returns:
            A list of search results.
        """
        # If max_results is the default, check environment variable
        if max_results is None:
            max_results = int(os.environ.get("MAX_SOURCES", 10))

        logger.info(f"ExaSearch: Searching with query:{os.linesep*2}```{self.query}{os.linesep}```")

        results: SearchResponse[_Result] = self.client.search(
            self.query,
            type=search_type,
            use_autoprompt=use_autoprompt,
            num_results=max_results,
            **filters,
        )

        search_response: list[dict[str, Any]] = [
            {
                "href": result.url,
                "body": getattr(result, "text", ""),
                #   "title": result.title if hasattr(result, "title") else "",
                #   "published_date": result.published_date if hasattr(result, "published_date") else None,
                #   "score": result.score if hasattr(result, "score") else None,
            }
            for result in results.results
        ]
        return search_response
