from __future__ import annotations

import importlib.util
import os

VALID_RETRIEVERS: list[str] = [
    "arxiv",
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
    "tavily",
    "pubmed_central",
]


def check_pkg(pkg: str) -> None:
    """Checks if a package is installed.

    Args:
        pkg: The name of the package to check.
    """
    if not importlib.util.find_spec(pkg):
        pkg_kebab: str = pkg.replace("_", "-")
        raise ImportError(f"Unable to import {pkg_kebab}. Please install with " f"`pip install -U {pkg_kebab}`")


# Get a list of all retriever names to be used as validators for supported retrievers
def get_all_retriever_names() -> list[str]:
    """Gets a list of all retriever names to be used as validators for supported retrievers."""
    try:
        current_dir: str = os.path.dirname(__file__)

        all_items: list[str] = os.listdir(current_dir)

        # Filter out only the directories, excluding __pycache__
        retrievers: list[str] = [item for item in all_items if os.path.isdir(os.path.join(current_dir, item))]
    except Exception as e:
        print(f"Error in get_all_retriever_names: {e}")
        return VALID_RETRIEVERS
    else:
        return retrievers
