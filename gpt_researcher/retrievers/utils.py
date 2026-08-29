"""Utility functions for GPT Researcher retrievers.

This module provides helper functions and constants used by the
various search retriever implementations.
"""

import importlib.util
import inspect
import logging
import os
import sys
from typing import List, Optional

logger = logging.getLogger(__name__)

async def stream_output(log_type, step, content, websocket=None, with_data=False, data=None):
    """
    Stream output to the client.
    
    Args:
        log_type (str): The type of log
        step (str): The step being performed
        content (str): The content to stream
        websocket: The websocket to stream to
        with_data (bool): Whether to include data
        data: Additional data to include
    """
    if websocket:
        try:
            if with_data:
                await websocket.send_json({
                    "type": log_type,
                    "step": step,
                    "content": content,
                    "data": data
                })
            else:
                await websocket.send_json({
                    "type": log_type,
                    "step": step,
                    "content": content
                })
        except Exception as e:
            logger.error(f"Error streaming output: {e}")

def check_pkg(pkg: str) -> None:
    """
    Checks if a package is installed and raises an error if not.
    
    Args:
        pkg (str): The package name
    
    Raises:
        ImportError: If the package is not installed
    """
    if not importlib.util.find_spec(pkg):
        pkg_kebab = pkg.replace("_", "-")
        raise ImportError(
            f"Unable to import {pkg_kebab}. Please install with "
            f"`pip install -U {pkg_kebab}`"
        )

# Valid retrievers for fallback
VALID_RETRIEVERS = [
    "tavily",
    "groundroute",
    "custom",
    "duckduckgo",
    "searchapi",
    "serper",
    "serpapi",
    "google",
    "searx",
    "bing",
    "brave",
    "arxiv",
    "semantic_scholar",
    "pubmed_central",
    "exa",
    "crw",
    "getxapi",
    "mcp",
    "xquik",
    "openalex",
    "mock"
]

def get_all_retriever_names():
    """
    Get all available retriever names
    :return: List of all available retriever names
    :rtype: list
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Get all items in the current directory
        all_items = os.listdir(current_dir)
        
        # Filter out only the directories, excluding __pycache__
        retrievers = [
            item for item in all_items 
            if os.path.isdir(os.path.join(current_dir, item)) and not item.startswith('__')
        ]
        
        return retrievers
    except Exception as e:
        logger.error(f"Error getting retrievers: {e}")
        return VALID_RETRIEVERS


def append_exclude_terms(query: str, exclude_terms: Optional[List[str]]) -> str:
    """Append Google-style exclusion operators to a search query.

    Single-word terms become ``-term``. Multi-word terms are quoted
    (``-"multi word"``).  If a multi-word term itself contains double
    quotes it is wrapped in single quotes instead.

    Returns the original query unchanged when *exclude_terms* is ``None``
    or empty.
    """
    if not exclude_terms:
        return query

    parts: List[str] = []
    for w in exclude_terms:
        w = w.strip()
        if not w:
            continue
        if " " in w:
            if '"' in w:
                parts.append(f"-'{w}'")
            else:
                parts.append(f'-"{w}"')
        else:
            parts.append(f"-{w}")

    return query + " " + " ".join(parts)


def supports_exclude_terms(retriever_cls) -> bool:
    """Check whether a retriever class explicitly accepts the ``exclude_terms`` kwarg.

    Returns ``True`` only when there is a named ``exclude_terms`` parameter.
    Classes that rely solely on ``**kwargs`` return ``False`` — they may
    swallow the argument silently but do not act on it.
    """
    try:
        params = inspect.signature(retriever_cls.__init__).parameters
    except (TypeError, ValueError):
        return False
    return "exclude_terms" in params
