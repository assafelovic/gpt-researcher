from __future__ import annotations

import os

from typing import TYPE_CHECKING, Any

from gpt_researcher.retrievers.utils import check_pkg

if TYPE_CHECKING:
    from exa_py.api import Result, SearchResponse

from gpt_researcher.retrievers.retriever_abc import RetrieverABC


class ExaSearch(RetrieverABC):
    """Exa API Retriever."""

    def __init__(self, query: str, query_domains: list[str] | None = None):
        """Initializes the ExaSearch object.

        Args:
            query (str): The search query.
            query_domains (list[str] | None): Optional list of domains to search within.
        """
        # This validation is necessary since exa_py is optional
        check_pkg("exa_py")
        from exa_py import Exa

        self.query: str = query
        self.query_domains: list[str] | None = query_domains
        self.api_key: str = self._retrieve_api_key()
        self.client: Exa = Exa(api_key=self.api_key)

    def _retrieve_api_key(self) -> str:
        """Retrieves the Exa API key from environment variables.

        Returns:
            str: The API key.

        Raises:
            Exception: If the API key is not found.
        """
        try:
            api_key: str = os.environ["EXA_API_KEY"]
        except KeyError:
            raise Exception("Exa API key not found. Please set the EXA_API_KEY environment variable. " "You can obtain your key from https://exa.ai/")
        return api_key

    def search(
        self,
        max_results: int = 10,
        use_autoprompt: bool = False,
        search_type: str = "neural",
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Searches the query using the Exa API.

        Args:
            max_results (int): The maximum number of results to return.
            use_autoprompt (bool): Whether to use autoprompting.
            search_type (str): The type of search (e.g., "neural", "keyword").
            **filters (Any): Additional filters (e.g., date range, domains).

        Returns:
            list[dict[str, Any]]: A list of search results.
        """
        # Add domains to filters if provided
        if self.query_domains:
            filters["include_domains"] = self.query_domains

        results: SearchResponse[Result] = self.client.search(
            self.query,
            type=search_type,
            use_autoprompt=use_autoprompt,
            num_results=max_results,
            include_domains=self.query_domains,
            **filters
        )

        search_response: list[dict[str, Any]] = [{"href": result.url, "body": result.text or ""} for result in results.results]
        return search_response

    def find_similar(
        self,
        url: str,
        exclude_source_domain: bool = False,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Finds similar documents to the provided URL using the Exa API.

        Args:
            url: The URL to find similar documents for.
            exclude_source_domain: Whether to exclude the source domain in the results.
            **filters: Additional filters.

        Returns:
            list[dict[str, Any]]: A list of similar documents.
        """
        results: SearchResponse[Result] = self.client.find_similar(
            url,
            exclude_source_domain=exclude_source_domain,
            **filters,
        )

        similar_response: list[dict[str, Any]] = [{"href": result.url, "body": result.text or ""} for result in results.results]
        return similar_response

    def get_contents(self, ids: list[str], **options: Any) -> list[dict[str, Any]]:
        """Retrieves the contents of the specified IDs using the Exa API.

        Args:
            ids: The IDs of the documents to retrieve.
            **options: Additional options for content retrieval.

        Returns:
            list[dict[str, Any]]: A list of document contents.
        """
        results: SearchResponse[Result] = self.client.get_contents(ids, **options)

        contents_response: list[dict[str, Any]] = [{"id": result.id, "content": result.text or ""} for result in results.results]
        return contents_response
