import logging

logger = logging.getLogger(__name__)

try:
    # Try to import langchain-mcp-adapters first to set the flag
    from langchain_mcp_adapters.client import MultiServerMCPClient
    HAS_MCP_ADAPTERS = True
    logger.debug("langchain-mcp-adapters is available")
except ImportError:
    HAS_MCP_ADAPTERS = False
    logger.debug("langchain-mcp-adapters is not available")

# Now try to import the MCPRetriever
try:
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