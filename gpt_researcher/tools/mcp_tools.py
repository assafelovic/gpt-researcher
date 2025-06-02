import asyncio
import logging
import os
from typing import List, Dict, Any, Optional

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain_mcp_adapters.tools import load_mcp_tools
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    
    try:
        from mcp.client.streamable_http import streamablehttp_client
        HAS_STREAMABLE_HTTP = True
    except ImportError:
        HAS_STREAMABLE_HTTP = False
        
    HAS_MCP_ADAPTERS = True
except ImportError:
    HAS_MCP_ADAPTERS = False

logger = logging.getLogger(__name__)


class MCPToolsProvider:
    """
    MCP Tools Provider using langchain-mcp-adapters
    
    This provider manages MCP servers and provides LangChain tools
    that can be used in the research process.
    """

    def __init__(self, mcp_configs: List[Dict[str, Any]], websocket=None):
        """
        Initialize the MCP Tools Provider.
        
        Args:
            mcp_configs (List[Dict[str, Any]]): List of MCP server configurations
            websocket: WebSocket for streaming logs
        """
        self.mcp_configs = mcp_configs or []
        self.websocket = websocket
        self.tools = []
        self.client = None
        
        if not HAS_MCP_ADAPTERS:
            logger.error("langchain-mcp-adapters not installed. MCP tools will not be available.")
            return
            
        if not self.mcp_configs:
            logger.warning("No MCP configurations provided")
            return
        
        # Convert mcp_configs to the format expected by MultiServerMCPClient
        self.server_configs = self._convert_configs()
        
    def _convert_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert GPT Researcher MCP configs to langchain-mcp-adapters format.
        
        Returns:
            Dict[str, Dict[str, Any]]: Server configurations for MultiServerMCPClient
        """
        server_configs = {}
        
        for i, config in enumerate(self.mcp_configs):
            # Generate server name
            server_name = config.get("server_name", f"mcp_server_{i+1}")
            
            # Build the server config
            server_config = {}
            
            # Handle transport type
            connection_type = config.get("connection_type", "stdio")
            server_config["transport"] = connection_type
            
            if connection_type == "stdio":
                # For stdio, we need command and args
                if config.get("server_command"):
                    server_config["command"] = config["server_command"]
                    
                    # Handle server_args
                    server_args = config.get("server_args", [])
                    if isinstance(server_args, str):
                        server_args = server_args.split()
                    server_config["args"] = server_args
                    
                    # Handle environment variables
                    server_env = config.get("server_env", {})
                    if server_env:
                        server_config["env"] = server_env
                        
            elif connection_type in ["streamable_http", "http"]:
                # For HTTP, we need URL
                if config.get("connection_url"):
                    server_config["url"] = config["connection_url"]
                    server_config["transport"] = "streamable_http"
                    
            elif connection_type == "websocket":
                # For WebSocket, we need URL
                if config.get("connection_url"):
                    server_config["url"] = config["connection_url"]
                    
            # Add authentication if provided
            if config.get("connection_token"):
                server_config["token"] = config["connection_token"]
                
            server_configs[server_name] = server_config
            
        return server_configs
        
    async def _stream_log(self, message: str, data: Any = None):
        """Stream a log message to the websocket if available."""
        logger.info(message)
        
        if self.websocket:
            try:
                from ..actions.utils import stream_output
                await stream_output(
                    "logs", 
                    "mcp_tools", 
                    message, 
                    self.websocket,
                    with_data=bool(data),
                    data=data
                )
            except Exception as e:
                logger.error(f"Error streaming log: {e}")
                
    async def initialize(self) -> bool:
        """
        Initialize the MCP tools by connecting to servers and loading tools.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if not HAS_MCP_ADAPTERS:
            await self._stream_log("❌ langchain-mcp-adapters not installed")
            return False
            
        if not self.server_configs:
            await self._stream_log("❌ No valid MCP server configurations found")
            return False
            
        try:
            await self._stream_log(f"🔧 Initializing {len(self.server_configs)} MCP server(s)")
            
            # Initialize the MultiServerMCPClient
            self.client = MultiServerMCPClient(self.server_configs)
            
            # Get tools from all servers
            self.tools = await self.client.get_tools()
            
            if self.tools:
                await self._stream_log(f"✅ Loaded {len(self.tools)} MCP tools")
                
                # Log tool names for debugging
                tool_names = [tool.name for tool in self.tools]
                await self._stream_log(f"🔧 Available tools: {', '.join(tool_names)}")
                
                return True
            else:
                await self._stream_log("⚠️ No tools loaded from MCP servers")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing MCP tools: {e}")
            await self._stream_log(f"❌ Error initializing MCP tools: {str(e)}")
            return False
            
    def get_tools(self) -> List:
        """
        Get the loaded LangChain tools.
        
        Returns:
            List: List of LangChain tools
        """
        return self.tools
        
    async def close(self):
        """Close the MCP client and clean up resources."""
        if self.client:
            try:
                # Since MultiServerMCPClient doesn't support context manager
                # or explicit close methods in langchain-mcp-adapters 0.1.0,
                # we just clear the reference and let garbage collection handle it
                await self._stream_log("🔧 Releasing MCP client reference")
            except Exception as e:
                logger.error(f"Error during MCP client cleanup: {e}")
                await self._stream_log(f"⚠️ Error during MCP client cleanup: {str(e)}")
            finally:
                # Always clear the reference
                self.client = None
                
    async def __aenter__(self):
        """Async context manager entry."""
        success = await self.initialize()
        if not success:
            raise RuntimeError("Failed to initialize MCP tools")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class MCPToolsManager:
    """
    Manager for MCP tools that integrates with the research flow.
    
    This is a singleton-like manager that handles the lifecycle of MCP tools
    throughout the research process.
    """
    
    _instance = None
    _provider = None
    
    @classmethod
    async def get_instance(cls, mcp_configs: List[Dict[str, Any]] = None, websocket=None):
        """
        Get or create the MCP tools manager instance.
        
        Args:
            mcp_configs: MCP server configurations
            websocket: WebSocket for streaming
            
        Returns:
            MCPToolsManager: The manager instance
        """
        if cls._instance is None:
            cls._instance = cls()
            
        # Initialize provider if needed
        if mcp_configs and cls._provider is None:
            cls._provider = MCPToolsProvider(mcp_configs, websocket)
            success = await cls._provider.initialize()
            if not success:
                cls._provider = None
                
        return cls._instance
        
    @classmethod
    async def get_tools(cls) -> List:
        """
        Get MCP tools if available.
        
        Returns:
            List: List of LangChain tools
        """
        if cls._provider:
            return cls._provider.get_tools()
        return []
        
    @classmethod
    async def close(cls):
        """Close the MCP provider and clean up."""
        if cls._provider:
            await cls._provider.close()
            cls._provider = None
        cls._instance = None 