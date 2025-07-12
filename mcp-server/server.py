"""GPT Researcher MCP Server

This script implements an MCP server for GPT Researcher, allowing AI assistants
to conduct web research and generate reports via the MCP protocol.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from gpt_researcher import GPTResearcher

# Load environment variables
load_dotenv()

from utils import (  # noqa: E402
    create_research_prompt,
    create_success_response,
    format_context_with_sources,
    format_sources_for_response,
    get_researcher_by_id,
    handle_exception,
    research_store,
    store_research_results,
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] - %(message)s",
)

logger: logging.Logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("GPT Researcher")

# Initialize researchers dictionary
if not hasattr(mcp, "researchers"):
    mcp.researchers = {}  # type: ignore[attr-defined]


@mcp.resource("research://{topic}")
async def research_resource(topic: str) -> str:
    """Provide research context for a given topic directly as a resource.

    This allows LLMs to access web-sourced information without explicit function calls.

    Args:
        topic: The research topic or query

    Returns:
        String containing the research context with source information
    """
    # Check if we've already researched this topic
    if topic in research_store:
        logger.info(f"Returning cached research for topic: {topic}")
        return research_store[topic]["context"]

    # If not, conduct the research
    logger.info(f"Conducting new research for resource on topic: {topic}")

    # Initialize GPT Researcher
    researcher = GPTResearcher(topic)

    try:
        # Conduct the research
        await researcher.conduct_research()

        # Get the context and sources
        context: str = researcher.get_research_context()
        sources: list[str] = researcher.get_research_sources()
        source_urls: list[str] = researcher.get_source_urls()

        # Format with sources included
        formatted_context: str = format_context_with_sources(topic, context, sources)

        # Store for future use
        store_research_results(topic, context, sources, source_urls, formatted_context)

        return formatted_context
    except Exception as e:
        return f"Error conducting research on '{topic}': {str(e)}"


@mcp.tool()
async def deep_research(query: str) -> dict[str, Any]:
    """Conduct a deep web research on a given query using GPT Researcher.

    Args:
        query: The research query or topic

    Returns:
        Dict containing research status, ID, and the actual research context and sources
        that can be used directly by LLMs for context enrichment

    Use this tool when you need time-sensitive, real-time information like stock prices, news, people, specific knowledge, etc.
    You must include citations that back your responses when using this tool.
    """
    # Generate a unique ID for this research session
    research_id: str = str(uuid.uuid4())

    logger.info(f"Conducting research on query: {research_id}...")

    # Initialize GPT Researcher
    researcher = GPTResearcher(query)

    try:
        # Conduct the research
        await researcher.conduct_research()

        # Get the context and sources
        context: str = researcher.get_research_context()
        sources: list[str] = researcher.get_research_sources()
        source_urls: list[str] = researcher.get_source_urls()

        # Format with sources included
        formatted_context: str = format_context_with_sources(query, context, sources)

        # Store for future use
        store_research_results(query, context, sources, source_urls, formatted_context)

    except Exception as e:
        return f"Error conducting research on '{query}': {str(e)}"

    else:
        return formatted_context


@mcp.tool()
async def write_report(
    query: str,
    custom_prompt: str | None = None,
) -> dict[str, Any]:
    """Generate a report based on previously conducted research.

    Args:
        query (str): The research query or topic
        custom_prompt (str | None): Optional custom prompt for report generation

    Returns:
        dict[str, Any] containing the report content and metadata
    """
    # Generate a unique ID for this research session
    research_id = str(uuid.uuid4())

    logger.info(f"Generating report for research ID: {research_id}")

    # Initialize GPT Researcher
    researcher = GPTResearcher(query)

    # Start research
    try:
        await researcher.conduct_research()
        mcp.researchers[research_id] = researcher
        logger.info(f"Research completed for ID: {research_id}")

        # Get the research context and sources
        context: list[dict[str, Any]] = researcher.get_research_context()
        sources: list[str] = researcher.get_research_sources()
        source_urls: list[str] = researcher.get_source_urls()

        # Store in the research store for the resource API
        store_research_results(query, context, sources, source_urls)

        return create_success_response(
            {
                "research_id": research_id,
                "query": query,
                "source_count": len(sources),
                "context": context,
                "sources": format_sources_for_response(sources),
                "source_urls": source_urls,
            }
        )
    except Exception as e:
        return handle_exception(e, "Research")


@mcp.tool()
async def write_report(
    research_id: str,
    custom_prompt: str | None = None,
) -> dict[str, Any]:
    """Generate a report based on previously conducted research.

    Args:
        research_id: The ID of the research session from conduct_research
        custom_prompt: Optional custom prompt for report generation

    Returns:
        dict[str, Any] containing the report content and metadata
    """
    success, researcher, error = get_researcher_by_id(mcp.researchers, research_id)
    if not success:
        return error

    logger.info(f"Generating report for research ID: {research_id}")

    try:
        # Generate report
        report: str = await researcher.write_report(custom_prompt=custom_prompt)

        # Get additional information
        sources: list[str] = researcher.get_research_sources()
        costs: float = researcher.get_costs()

        return create_success_response({
            "report": report,
            "source_count": len(sources),
            "costs": costs
        })
    except Exception as e:
        return handle_exception(e, "Report generation")


@mcp.tool()
async def get_research_sources(research_id: str) -> dict[str, Any]:
    """Get the sources used in the research.

    Args:
        research_id: The ID of the research session

    Returns:
        Dict containing the research sources
    """
    success, researcher, error = get_researcher_by_id(mcp.researchers, research_id)
    if not success:
        return error

    sources: list[str] = researcher.get_research_sources()
    source_urls: list[str] = researcher.get_source_urls()

    return create_success_response(
        {"sources": format_sources_for_response(sources), "source_urls": source_urls}
    )


@mcp.tool()
async def get_research_context(research_id: str) -> dict[str, Any]:
    """Get the full context of the research.

    Args:
        research_id (str): The ID of the research session

    Returns:
        dict[str, Any] containing the research context
    """
    success, researcher, error = get_researcher_by_id(mcp.researchers, research_id)
    if not success:
        return error

    context: str = researcher.get_research_context()

    return create_success_response({"context": context})


@mcp.prompt()
def research_query(
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
    return create_research_prompt(topic, goal, report_format)


def run_server():
    """Run the MCP server using FastMCP's built-in event loop handling."""
    # Check if API keys are set
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not found. Please set it in your .env file.")
        return

    # Add startup message
    logger.info("Starting GPT Researcher MCP Server...")
    print(
        "🚀 GPT Researcher MCP Server starting... Check researcher_mcp_server.log for details"
    )  # noqa: E501 # pylint: disable=line-too-long

    # Let FastMCP handle the event loop
    try:
        mcp.run()
        # Note: If we reach here, the server has stopped
        logger.info("MCP Server has stopped")
    except Exception as e:
        logger.error(f"Error running MCP server: {str(e)}")
        print(f"❌ MCP Server error: {str(e)}")
        return
    print("✅ MCP Server stopped")


if __name__ == "__main__":
    # Use the non-async approach to avoid asyncio nesting issues
    run_server()
