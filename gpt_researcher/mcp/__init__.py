"""
MCP (Model Context Protocol) Integration for GPT Researcher

This module provides comprehensive MCP integration including:
- Client management for MCP servers
- Tool selection and execution
- Research execution with MCP tools
- Streaming support for real-time updates
"""

import logging

logger = logging.getLogger(__name__)

try:
    # Check if langchain-mcp-adapters is available
    from langchain_mcp_adapters.client import MultiServerMCPClient
    HAS_MCP_ADAPTERS = True
    logger.debug("langchain-mcp-adapters is available")
    
    # Import core MCP components
    from .client import MCPClientManager
    from .tool_selector import MCPToolSelector
    from .research import MCPResearchSkill
    from .streaming import MCPStreamer
    
    __all__ = [
        "MCPClientManager",
        "MCPToolSelector", 
        "MCPResearchSkill",
        "MCPStreamer",
        "HAS_MCP_ADAPTERS"
    ]
    
except ImportError as e:
    logger.warning(f"MCP dependencies not available: {e}")
    HAS_MCP_ADAPTERS = False
    __all__ = ["HAS_MCP_ADAPTERS"]
    
except Exception as e:
    logger.error(f"Unexpected error importing MCP components: {e}")
    HAS_MCP_ADAPTERS = False
    __all__ = ["HAS_MCP_ADAPTERS"] 