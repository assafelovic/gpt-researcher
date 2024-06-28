import os

from exa_py import Exa


class ExaSearch:
    """
    Exa API Retriever
    """

    def __init__(self, query):
        """
        Initializes the ExaSearch object.
        Args:
            query: The search query.
        """
        self.query = query
        self.api_key = self._retrieve_api_key()
        self.client = Exa(api_key=self.api_key)

    def _retrieve_api_key(self):
        """
        Retrieves the Exa API key from environment variables.
        Returns:
            The API key.
        Raises:
            Exception: If the API key is not found.
        """
        try:
            api_key = os.environ["EXA_API_KEY"]
        except KeyError:
            raise Exception(
                "Exa API key not found. Please set the EXA_API_KEY environment variable. "
                "You can obtain your key from https://exa.ai/"
            )
        return api_key

    def search(
        self, max_results=10, use_autoprompt=False, search_type="neural", **filters
    ):
        """
        Searches the query using the Exa API.
        Args:
            max_results: The maximum number of results to return.
            use_autoprompt: Whether to use autoprompting.
            search_type: The type of search (e.g., "neural", "keyword").
            **filters: Additional filters (e.g., date range, domains).
        Returns:
            A list of search results.
        """
        results = self.client.search(
            self.query,
            type=search_type,
            use_autoprompt=use_autoprompt,
            num_results=max_results,
            **filters
        )

        search_response = [
            {"href": result.url, "body": result.text} for result in results.results
        ]
        return search_response

    def find_similar(self, url, exclude_source_domain=False, **filters):
        """
        Finds similar documents to the provided URL using the Exa API.
        Args:
            url: The URL to find similar documents for.
            exclude_source_domain: Whether to exclude the source domain in the results.
            **filters: Additional filters.
        Returns:
            A list of similar documents.
        """
        results = self.client.find_similar(
            url, exclude_source_domain=exclude_source_domain, **filters
        )

        similar_response = [
            {"href": result.url, "body": result.text} for result in results.results
        ]
        return similar_response

    def get_contents(self, ids, **options):
        """
        Retrieves the contents of the specified IDs using the Exa API.
        Args:
            ids: The IDs of the documents to retrieve.
            **options: Additional options for content retrieval.
        Returns:
            A list of document contents.
        """
        results = self.client.get_contents(ids, **options)

        contents_response = [
            {"id": result.id, "content": result.text} for result in results.results
        ]
        return contents_response
