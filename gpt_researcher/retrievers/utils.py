from __future__ import annotations

import importlib.util
import os

from typing import TYPE_CHECKING

from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging

# Map our retriever names to langchain equivalents
LANGCHAIN_RETRIEVERS: dict[str, str] = {
    "arxiv": "ArxivRetriever",
    "pubmed": "PubMedRetriever",
    "tavily": "TavilySearchAPIRetriever",
    "you": "YouRetriever",
}


logger: logging.Logger = get_formatted_logger(__name__)


VALID_RETRIEVERS: list[str] = [
    *tuple(
        {
            "bing",
            "custom",
            "duckduckgo",
            "exa",
            "google",
            "searchapi",
            "searx",
            "semantic_scholar",
            "serpapi",
            "serper",
            # Add LangChain retrievers
            *LANGCHAIN_RETRIEVERS.keys(),
        }
    ),
]


def check_pkg(pkg: str) -> None:
    """Check if a package is installed.

    Args:
        pkg: Package name to check

    Raises:
        ImportError: If package is not installed
    """
    if not importlib.util.find_spec(pkg):
        pkg_kebab: str = pkg.replace("_", "-")
        raise ImportError(f"Unable to import {pkg_kebab}. Please install with `pip install -U {pkg_kebab}`")


def get_all_retriever_names() -> list[str]:
    """Get a list of all available retriever names.

    Returns:
        List of retriever names
    """
    try:
        current_dir: str = os.path.dirname(__file__)
        all_items: list[str] = os.listdir(current_dir)

        # Filter out only the directories, excluding __pycache__ and hidden dirs
        retrievers: list[str] = [
            item
            for item in all_items
            if os.path.isdir(os.path.join(current_dir, item)) and not item.startswith("__") and not item.startswith(".")
        ]
    except Exception as e:
        logger.exception(f"Error in get_all_retriever_names: {e.__class__.__name__}: {e}")
        retrievers = VALID_RETRIEVERS

    return retrievers
