"""
MCP Retriever Module

This module contains only the MCP retriever implementation.
The core MCP functionality has been moved to gpt_researcher.mcp module.
"""
import logging

logger = logging.getLogger(__name__)

try:
    # Check if langchain-mcp-adapters is available
    from langchain_mcp_adapters.client import MultiServerMCPClient
    HAS_MCP_ADAPTERS = True
    logger.debug("langchain-mcp-adapters is available")
    
    # Import the retriever
    from .retriever import MCPRetriever
    __all__ = ["MCPRetriever"]
    logger.debug("MCPRetriever imported successfully")
    
except ImportError as e:
    # Log the specific import error for debugging
    logger.warning(f"Failed to import MCPRetriever: {e}")
    # MCP package not installed or other import error, provide a placeholder
    MCPRetriever = None
    __all__ = []
except Exception as e:
    # Catch any other exception that might occur
    logger.error(f"Unexpected error importing MCPRetriever: {e}")
    MCPRetriever = None
    __all__ = [] 