"""Terminal exceptions for fail-fast research safeguards."""


class RetrievalFailureError(Exception):
    """Raised when repeated sub-queries fail to produce retrievable sources."""

    def __init__(self, failed_queries: list[str]):
        self.failed_queries = failed_queries
        query_list = ", ".join(failed_queries)
        super().__init__(
            f"Retrieval failed for consecutive sub-queries: {query_list}"
        )


class BudgetExceededError(BaseException):
    """Raised when the shared research budget exceeds MAX_COST_USD."""

    def __init__(self, max_cost_usd: float, total_cost_usd: float):
        self.max_cost_usd = max_cost_usd
        self.total_cost_usd = total_cost_usd
        super().__init__(
            f"Research budget exceeded: ${total_cost_usd:.6f} > ${max_cost_usd:.6f}"
        )
