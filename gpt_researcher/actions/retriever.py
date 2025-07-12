from __future__ import annotations

import os

from gpt_researcher.config import Config
from gpt_researcher.retrievers.retriever_abc import RetrieverABC


def get_retriever(retriever: str) -> type[RetrieverABC] | None:
    """Gets the retriever.

    Args:
        retriever (str): retriever name

    Returns:
        retriever: Retriever class
    """
    match retriever:
        case "google":
            from gpt_researcher.retrievers import GoogleSearch

            return GoogleSearch
        case "searx":
            from gpt_researcher.retrievers import SearxSearch

            return SearxSearch
        case "searchapi":
            from gpt_researcher.retrievers import SearchApiSearch

            return SearchApiSearch
        case "serpapi":
            from gpt_researcher.retrievers import SerpApiSearch

            return SerpApiSearch
        case "serper":
            from gpt_researcher.retrievers import SerperSearch

            return SerperSearch
        case "duckduckgo":
            from gpt_researcher.retrievers import Duckduckgo

            return Duckduckgo
        case "bing":
            from gpt_researcher.retrievers import BingSearch

            return BingSearch
        case "arxiv":
            from gpt_researcher.retrievers import ArxivSearch

            return ArxivSearch
        case "tavily":
            from gpt_researcher.retrievers import TavilySearch

            return TavilySearch
        case "exa":
            from gpt_researcher.retrievers import ExaSearch

            return ExaSearch
        case "semantic_scholar":
            from gpt_researcher.retrievers import SemanticScholarSearch

            return SemanticScholarSearch
        case "pubmed_central":
            from gpt_researcher.retrievers import PubMedCentralSearch

            return PubMedCentralSearch
        case "custom":
            from gpt_researcher.retrievers import CustomRetriever

            return CustomRetriever
        case "mcp":
            from gpt_researcher.retrievers import MCPRetriever

            return MCPRetriever

        case _:
            return None


def _get_available_fallback_retrievers() -> list[str]:
    """Get a list of available fallback retrievers based on API key availability.

    Returns retrievers in order of preference (free/no-API-key first).
    """
    fallback_retrievers: list[str] = []

    # Always available (no API key required)
    fallback_retrievers.append("duckduckgo")
    fallback_retrievers.append("arxiv")  # For academic queries

    # Add retrievers based on available API keys
    if os.environ.get("BING_API_KEY"):
        fallback_retrievers.append("bing")

    if os.environ.get("GOOGLE_API_KEY") and os.environ.get("GOOGLE_CX_KEY"):
        fallback_retrievers.append("google")

    if os.environ.get("SERPAPI_API_KEY"):
        fallback_retrievers.append("serpapi")

    if os.environ.get("SERPER_API_KEY"):
        fallback_retrievers.append("serper")

    if os.environ.get("SEARCHAPI_API_KEY"):
        fallback_retrievers.append("searchapi")

    if os.environ.get("EXA_API_KEY"):
        fallback_retrievers.append("exa")

    # Add Tavily as last resort if API key is available
    if os.environ.get("TAVILY_API_KEY"):
        fallback_retrievers.append("tavily")

    return fallback_retrievers


def get_retrievers(headers: dict[str, str], cfg: Config) -> list[type[RetrieverABC]]:
    """Determine which retriever(s) to use based on headers, config, or default.
    Automatically configures fallback retrievers for robustness.

    Args:
        headers (dict): The headers dictionary
        cfg: The configuration object

    Returns:
        list[type[RetrieverABC]]: A list of retriever classes to be used for searching.
    """
    primary_retrievers: list[str] = []

    # Check headers first for multiple retrievers
    if headers.get("retrievers"):
        primary_retrievers = [r.strip() for r in headers.get("retrievers").split(",")]
    # If not found, check headers for a single retriever
    elif headers.get("retriever"):
        primary_retrievers = [headers.get("retriever").strip()]
    # If not in headers, check config for multiple retrievers
    elif cfg.retrievers:
        # Handle both list and string formats for config retrievers
        if isinstance(cfg.retrievers, str):
            retrievers = cfg.retrievers.split(",")
        else:
            retrievers = cfg.retrievers
        # Strip whitespace from each retriever name
        retrievers = [r.strip() for r in retrievers]
        primary_retrievers = cfg.retrievers
    # If not found, check config for a single retriever
    elif hasattr(cfg, "retriever") and getattr(cfg, "retriever", None):
        primary_retrievers = [getattr(cfg, "retriever")]
    # If still not set, use default retriever
    else:
        primary_retrievers = [get_default_retriever().__name__.lower()]

    # Get available fallback retrievers
    available_fallbacks: list[str] = _get_available_fallback_retrievers()

    # Combine primary and fallback retrievers, avoiding duplicates
    all_retrievers: list[str] = []

    # Add primary retrievers first
    for retriever_name in primary_retrievers:
        retriever_name = retriever_name.lower().strip()
        if retriever_name not in [r.lower() for r in all_retrievers]:
            all_retrievers.append(retriever_name)

    # Add fallback retrievers that aren't already included
    for fallback in available_fallbacks:
        if fallback.lower() not in [r.lower() for r in all_retrievers]:
            all_retrievers.append(fallback)

    # Convert retriever names to actual retriever classes
    retriever_classes: list[type[RetrieverABC]] = []
    for retriever_name in all_retrievers:
        retriever_class: type[RetrieverABC] | None = get_retriever(retriever_name)
        if retriever_class:
            retriever_classes.append(retriever_class)

    # Ensure we always have at least one retriever
    if not retriever_classes:
        retriever_classes = [get_default_retriever()]

    print(f"Configured retrievers: {[r.__name__ for r in retriever_classes]}")
    return retriever_classes


def get_default_retriever() -> type[RetrieverABC]:
    from gpt_researcher.retrievers import TavilySearch

    return TavilySearch
