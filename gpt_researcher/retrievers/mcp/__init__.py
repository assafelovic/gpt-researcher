try:
    from .mcp_retriever import MCPRetriever
    __all__ = ["MCPRetriever"]
except ImportError:
    # MCP package not installed, provide a placeholder
    MCPRetriever = None
    __all__ = [] 