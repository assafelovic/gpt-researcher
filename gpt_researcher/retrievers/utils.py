from __future__ import annotations

import importlib.util
import logging
import os
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

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
    "mcp",
    "mock"
]

async def stream_output(
    log_type: str,
    step: str,
    content: str,
    websocket: WebSocket | None = None,
    with_data: bool = False,
    data: Any | None = None,
):
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

# Get a list of all retriever names to be used as validators for supported retrievers
def get_all_retriever_names() -> list[str]:
    """Gets a list of all retriever names to be used as validators for supported retrievers."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Get all items in the current directory
        all_items = os.listdir(current_dir)

        # Filter out only the directories, excluding __pycache__
        retrievers = [
            item for item in all_items
            if os.path.isdir(os.path.join(current_dir, item)) and not item.startswith('__')
        ]

    except Exception as e:
        logger.error(f"Error getting retrievers: {e.__class__.__name__}: {e}")
        return VALID_RETRIEVERS

    else:
        return retrievers
