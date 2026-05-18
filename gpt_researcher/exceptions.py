"""Terminal exceptions for fail-fast research safeguards."""


class RetrievalFailureError(Exception):
    """Raised when repeated sub-queries fail to produce retrievable sources."""

    def __init__(self, failed_queries: list[str]):
        self.failed_queries = failed_queries
        query_list = ", ".join(failed_queries)
        super().__init__(
            f"Retrieval failed for consecutive sub-queries: {query_list}"
        )
