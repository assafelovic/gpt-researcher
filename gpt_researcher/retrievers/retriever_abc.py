from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

class RetrieverABC(ABC):
    """Abstract base class for retrievers."""

    @abstractmethod
    def __init__(self, query: str | None = None, query_domains: list[str] | None = None, *args: Any, **kwargs: Any) -> None:
        ...

    @abstractmethod
    def search(self, query: str, max_results: int | None = None) -> list[dict[str, Any]]:
        ...
