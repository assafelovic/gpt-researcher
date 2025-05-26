"""GPT Researcher MCP Server Utilities

This module provides utility functions and helpers for the GPT Researcher MCP Server.
"""
from __future__ import annotations

import importlib.util
import logging
import sys
from typing import Any

if importlib.util.find_spec("loguru"):
    from loguru import logger
else:
    logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)
# Configure logging for console only (no file logging)
logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])

# Research store to track ongoing research topics and contexts
research_store: dict[str, Any] = {}

# API Response Utilities
def create_error_response(message: str) -> dict[str, Any]:
    """Create a standardized error response"""
    return {"status": "error", "message": message}


def create_success_response(data: dict[str, Any]) -> dict[str, Any]:
    """Create a standardized success response"""
    return {"status": "success", **data}


def handle_exception(e: Exception, operation: str) -> dict[str, Any]:
    """Handle exceptions in a consistent way

    Args:
        e: The exception to handle
        operation: The operation that failed

    Returns:
        A standardized error response
    """
    error_message: str = str(e)
    logger.error(f"{operation} failed: {error_message}")
    return create_error_response(error_message)


def get_researcher_by_id(
    researchers_dict: dict[str, Any],
    research_id: str,
) -> tuple[bool, Any, dict[str, Any]]:
    """Helper function to retrieve a researcher by ID.

    Args:
        researchers_dict: Dictionary of research objects
        research_id: The ID of the research session

    Returns:
        Tuple containing (success, researcher_object, error_response)
    """
    if not researchers_dict or research_id not in researchers_dict:
        return False, None, create_error_response("Research ID not found. Please conduct research first.")
    return True, researchers_dict[research_id], {}


def format_sources_for_response(
    sources: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Format source information for API responses.

    Args:
        sources: List of source dictionaries

    Returns:
        Formatted source list for API responses
    """
    return [
        {
            "title": source.get("title", "Unknown"),
            "url": source.get("url", ""),
            "content_length": len(source.get("content", ""))
        }
        for source in sources
    ]


def format_context_with_sources(
    topic: str,
    context: str,
    sources: list[dict[str, Any]],
) -> str:
    """Format research context with sources for display.

    Args:
        topic: Research topic
        context: Research context
        sources: List of sources

    Returns:
        Formatted context string with sources
    """
    formatted_context = f"## Research: {topic}\n\n{context}\n\n"
    formatted_context += "## Sources:\n"
    for i, source in enumerate(sources):
        formatted_context += f"{i+1}. {source.get('title', 'Unknown')}: {source.get('url', '')}\n"
    return formatted_context


def store_research_results(
    topic: str,
    context: str,
    sources: list[dict[str, Any]],
    source_urls: list[str],
    formatted_context: str | None = None,
):
    """Store research results in the research store.

    Args:
        topic: Research topic
        context: Research context
        sources: List of sources
        source_urls: List of source URLs
        formatted_context: Optional pre-formatted context
    """
    research_store[topic] = {
        "context": formatted_context or context,
        "sources": sources,
        "source_urls": source_urls
    }


def create_research_prompt(
    topic: str,
    goal: str,
    report_format: str = "research_report",
) -> str:
    """Create a research query prompt for GPT Researcher.

    Args:
        topic: The topic to research
        goal: The goal or specific question to answer
        report_format: The format of the report to generate

    Returns:
        A formatted prompt for research
    """

    return f"""
    Please research the following topic: {topic}

    Goal: {goal}

    You have two methods to access web-sourced information:

    1. Use the "research://{topic}" resource to directly access context about this topic if it exists
       or if you want to get straight to the information without tracking a research ID.

    2. Use the conduct_research tool to perform new research and get a research_id for later use.
       This tool also returns the context directly in its response, which you can use immediately.

    After getting context, you can:
    - Use it directly in your response
    - Use the write_report tool with a custom prompt to generate a structured {report_format}

    You can also use get_research_sources to view additional details about the information sources."""
