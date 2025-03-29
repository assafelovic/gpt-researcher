#!/usr/bin/env python3
"""
GPT Researcher MCP Server

This script implements an MCP server for GPT Researcher, allowing AI assistants
to conduct web research and generate reports via the MCP protocol.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv
from loguru import logger
from mcp.server.fastmcp import FastMCP
from gpt_researcher import GPTResearcher

# Load environment variables
load_dotenv()

# Configure logging for console only (no file logging)
logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])

# Initialize FastMCP server
mcp = FastMCP("GPT Researcher")


# Track ongoing research topics and contexts
research_store = {}


@mcp.resource("research://{topic}")
async def research_resource(topic: str) -> str:
    """
    Provide research context for a given topic directly as a resource.
    
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
    researcher = GPTResearcher(topic, "resource_report")
    
    try:
        # Conduct the research
        await researcher.conduct_research()
        
        # Get the context and sources
        context = researcher.get_research_context()
        sources = researcher.get_research_sources()
        source_urls = researcher.get_source_urls()
        
        # Format with sources included
        formatted_context = f"## Research: {topic}\n\n{context}\n\n"
        formatted_context += "## Sources:\n"
        for i, source in enumerate(sources):
            formatted_context += f"{i+1}. {source.get('title', 'Unknown')}: {source.get('url', '')}\n"
        
        # Store for future use
        research_store[topic] = {
            "context": formatted_context,
            "sources": sources,
            "source_urls": source_urls
        }
        
        return formatted_context
    except Exception as e:
        logger.error(f"Research resource failed: {str(e)}")
        return f"Error conducting research on '{topic}': {str(e)}"


@mcp.tool()
async def conduct_research(query: str, report_type: str = "research_report") -> Dict[str, Any]:
    """
    Conduct research on a given query using GPT Researcher.
    
    Args:
        query: The research query or topic
        report_type: Type of report to generate (research_report, resource_report, outline_report)
        
    Returns:
        Dict containing research status, ID, and the actual research context and sources
        that can be used directly by LLMs for context enrichment
    """
    logger.info(f"Conducting research on query: {query} with report type: {report_type}")
    
    # Store the researcher in the server's shared state
    if not hasattr(mcp, "researchers"):
        mcp.researchers = {}
    
    # Generate a unique ID for this research session
    import uuid
    research_id = str(uuid.uuid4())
    
    # Initialize GPT Researcher
    researcher = GPTResearcher(query, report_type)
    
    # Start research
    try:
        await researcher.conduct_research()
        mcp.researchers[research_id] = researcher
        logger.info(f"Research completed for ID: {research_id}")
        
        # Get the research context and sources
        context = researcher.get_research_context()
        sources = researcher.get_research_sources()
        source_urls = researcher.get_source_urls()
        
        # Store in the research store for the resource API
        research_store[query] = {
            "context": context,
            "sources": sources,
            "source_urls": source_urls
        }
        
        return {
            "status": "completed",
            "research_id": research_id,
            "report_type": report_type,
            "query": query,
            "source_count": len(sources),
            "context": context,
            "sources": [
                {
                    "title": source.get("title", "Unknown"),
                    "url": source.get("url", ""),
                    "content_length": len(source.get("content", ""))
                }
                for source in sources
            ],
            "source_urls": source_urls
        }
    except Exception as e:
        logger.error(f"Research failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@mcp.tool()
async def write_report(research_id: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a report based on previously conducted research.
    
    Args:
        research_id: The ID of the research session from conduct_research
        custom_prompt: Optional custom prompt for report generation
        
    Returns:
        Dict containing the report content and metadata
    """
    if not hasattr(mcp, "researchers") or research_id not in mcp.researchers:
        return {"status": "error", "message": "Research ID not found. Please conduct research first."}
    
    researcher = mcp.researchers[research_id]
    logger.info(f"Generating report for research ID: {research_id}")
    
    try:
        # Generate report
        report = await researcher.write_report(custom_prompt=custom_prompt)
        
        # Get additional information
        sources = researcher.get_research_sources()
        costs = researcher.get_costs()
        
        return {
            "status": "success",
            "report": report,
            "source_count": len(sources),
            "costs": costs
        }
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@mcp.tool()
async def get_research_sources(research_id: str) -> Dict[str, Any]:
    """
    Get the sources used in the research.
    
    Args:
        research_id: The ID of the research session
        
    Returns:
        Dict containing the research sources
    """
    if not hasattr(mcp, "researchers") or research_id not in mcp.researchers:
        return {"status": "error", "message": "Research ID not found. Please conduct research first."}
    
    researcher = mcp.researchers[research_id]
    sources = researcher.get_research_sources()
    source_urls = researcher.get_source_urls()
    
    return {
        "status": "success",
        "sources": [
            {
                "title": source.get("title", "Unknown"),
                "url": source.get("url", ""),
                "content_length": len(source.get("content", ""))
            }
            for source in sources
        ],
        "source_urls": source_urls
    }


@mcp.tool()
async def get_research_context(research_id: str) -> Dict[str, Any]:
    """
    Get the full context of the research.
    
    Args:
        research_id: The ID of the research session
        
    Returns:
        Dict containing the research context
    """
    if not hasattr(mcp, "researchers") or research_id not in mcp.researchers:
        return {"status": "error", "message": "Research ID not found. Please conduct research first."}
    
    researcher = mcp.researchers[research_id]
    context = researcher.get_research_context()
    
    return {
        "status": "success",
        "context": context
    }


@mcp.prompt()
def research_query(topic: str, goal: str, report_format: str = "research_report") -> str:
    """
    Create a research query prompt for GPT Researcher.
    
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
    
    You can also use get_research_sources to view additional details about the information sources.
    """


def run_server():
    """Run the MCP server using FastMCP's built-in event loop handling."""
    # Check if API keys are set
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not found. Please set it in your .env file.")
        return
    
    # Add startup message
    logger.info("Starting GPT Researcher MCP Server...")
    print("🚀 GPT Researcher MCP Server starting... Check researcher_mcp_server.log for details")
    
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
