from __future__ import annotations

from typing import Any

from gpt_researcher.config.config import Config


    """Gets the retriever.

def get_retriever(retriever):
    Args:
        retriever: retriever name

    Returns:
        retriever: Retriever class

    """
    match retriever:
        case "google":
            from gpt_researcher.retrievers import GoogleSearch

            retriever_cls = GoogleSearch
        case "searx":
            from gpt_researcher.retrievers import SearxSearch

            retriever_cls = SearxSearch
        case "searchapi":
            from gpt_researcher.retrievers import SearchApiSearch

            retriever_cls = SearchApiSearch
        case "serpapi":
            from gpt_researcher.retrievers import SerpApiSearch

            retriever_cls = SerpApiSearch
        case "serper":
            from gpt_researcher.retrievers import SerperSearch

            retriever_cls = SerperSearch
        case "duckduckgo":
            from gpt_researcher.retrievers import Duckduckgo

            retriever_cls = Duckduckgo
        case "bing":
            from gpt_researcher.retrievers import BingSearch

            retriever_cls = BingSearch
        case "arxiv":
            from gpt_researcher.retrievers import ArxivSearch

            retriever_cls = ArxivSearch
        case "tavily":
            from gpt_researcher.retrievers import TavilySearch

            retriever_cls = TavilySearch
        case "exa":
            from gpt_researcher.retrievers import ExaSearch

            retriever_cls = ExaSearch
        case "semantic_scholar":
            from gpt_researcher.retrievers import SemanticScholarSearch

            retriever_cls = SemanticScholarSearch
        case "pubmed_central":
            from gpt_researcher.retrievers import PubMedCentralSearch

            retriever_cls = PubMedCentralSearch
        case "custom":
            from gpt_researcher.retrievers import CustomRetriever

            retriever_cls = CustomRetriever

        case _:
            retriever_cls = None

    return retriever_cls


def get_retrievers(headers, cfg):
    """Determine which retriever(s) to use based on headers, config, or default.

    Args:
        headers (dict): The headers dictionary
        cfg (Config): The configuration object

    Returns:
        list: A list of retriever classes to be used for searching.
    """
    # Check headers first for multiple retrievers
    if headers.get("retrievers"):
        retrievers = str(headers.get("retrievers", "")).split(",")
    # If not found, check headers for a single retriever
    elif headers.get("retriever"):
        retrievers = [headers.get("retriever")]
    # If not in headers, check config for multiple retrievers
    elif cfg.retrievers:
        retrievers = cfg.retrievers
    # If not found, check config for a single retriever
    elif cfg.retriever:  # pyright: ignore[reportAttributeAccessIssue]
        retrievers = [cfg.retriever]  # pyright: ignore[reportAttributeAccessIssue]
    # If still not set, use default retriever
    else:
        retrievers = [get_default_retriever().__name__]

    # Convert retriever names to actual retriever classes
    # Use get_default_retriever() as a fallback for any invalid retriever names
    return [get_retriever(r) or get_default_retriever() for r in retrievers]


def get_default_retriever(retriever):
    """Gets the default retriever."""
    from gpt_researcher.retrievers import TavilySearch

    return TavilySearch
