import asyncio
import logging
import os
from typing import List, Dict, Any, Optional, Tuple, Union

try:
    import mcp
    from mcp import ClientSession, StdioServerParameters, types
    from mcp.client.stdio import stdio_client
    
    # Import additional connection methods
    try:
        from mcp.client.websocket import websocket_client
        from mcp.client.http import http_client
        HAS_REMOTE_MCP = True
    except ImportError:
        HAS_REMOTE_MCP = False
        
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    HAS_REMOTE_MCP = False

logger = logging.getLogger(__name__)

class MCPRetriever:
    """
    Model Context Protocol (MCP) Retriever for GPT Researcher
    
    This retriever enables GPT Researcher to use MCP servers as data sources.
    MCP servers provide standardized access to tools, resources, and prompts.
    
    The retriever can connect to any MCP server that follows the protocol spec,
    including local servers and remote servers via WebSocket or HTTP.
    """

    def __init__(
        self, 
        query: str, 
        headers: Optional[Dict[str, str]] = None,
        query_domains: Optional[List[str]] = None,
        server_name: Optional[str] = None,
        server_command: Optional[str] = None,
        server_args: Optional[List[str]] = None,
        server_env: Optional[Dict[str, str]] = None,
        resource_uri_template: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        connection_type: Optional[str] = None,
        connection_url: Optional[str] = None,
        connection_token: Optional[str] = None,
    ):
        """
        Initialize the MCP Retriever.
        
        Args:
            query (str): The search query string.
            headers (dict, optional): Additional headers for configuration.
            query_domains (list, optional): List of domains to search (not directly used in MCP).
            server_name (str, optional): Name of the MCP server to connect to.
            server_command (str, optional): Command to start the MCP server.
            server_args (list, optional): Arguments to pass to the server command.
            server_env (dict, optional): Environment variables for the server.
            resource_uri_template (str, optional): URI template for accessing a resource.
            tool_name (str, optional): Name of the MCP tool to invoke.
            tool_args (dict, optional): Arguments to pass to the MCP tool.
            connection_type (str, optional): Type of connection (stdio, websocket, http).
            connection_url (str, optional): URL for WebSocket or HTTP connection.
            connection_token (str, optional): Authentication token for remote connections.
        """
        self.query = query
        self.headers = headers or {}
        self.query_domains = query_domains or []
        
        # MCP server configuration
        self.server_name = server_name or self.headers.get("mcp_server_name")
        self.server_command = server_command or self.headers.get("mcp_server_command")
        self.server_args = server_args or (
            self.headers.get("mcp_server_args", "").split() if self.headers.get("mcp_server_args") else []
        )
        self.server_env = server_env or {}
        
        # Get environment variables from headers
        for key, value in self.headers.items():
            if key.startswith("mcp_env_"):
                env_name = key[8:]  # Remove 'mcp_env_' prefix
                self.server_env[env_name] = value
        
        # Resource or tool configuration
        self.resource_uri_template = resource_uri_template or self.headers.get("mcp_resource_uri")
        self.tool_name = tool_name or self.headers.get("mcp_tool_name")
        self.tool_args = tool_args or {}
        
        # Parse tool arguments from headers
        for key, value in self.headers.items():
            if key.startswith("mcp_tool_arg_"):
                arg_name = key[13:]  # Remove 'mcp_tool_arg_' prefix
                self.tool_args[arg_name] = value
                
        # If query is provided and not in tool_args, add it
        if "query" not in self.tool_args and self.query:
            self.tool_args["query"] = self.query
            
        # Connection configuration
        self.connection_type = connection_type or self.headers.get("mcp_connection_type", "stdio")
        self.connection_url = connection_url or self.headers.get("mcp_connection_url")
        self.connection_token = connection_token or self.headers.get("mcp_connection_token")
            
        # Check if MCP is installed
        if not HAS_MCP:
            logger.warning(
                "The MCP Python package is not installed. Install it with 'pip install mcp' to use the MCP retriever."
            )
        # Check if remote MCP support is available
        elif self.connection_type in ["websocket", "http"] and not HAS_REMOTE_MCP:
            logger.warning(
                f"The MCP Python package does not support {self.connection_type} connections. "
                "Make sure you have the latest version installed."
            )

    async def _connect_to_server(self) -> Tuple[ClientSession, Any]:
        """
        Connect to an MCP server and return a session.
        
        Returns:
            Tuple[ClientSession, Any]: The MCP client session and additional context
        """
        if not HAS_MCP:
            raise ImportError("The MCP Python package is not installed. Install it with 'pip install mcp'.")
        
        # Use the appropriate connection method based on connection_type
        if self.connection_type == "websocket":
            if not HAS_REMOTE_MCP:
                raise ImportError("WebSocket connection requires mcp package with websocket support. Update your mcp package.")
            
            if not self.connection_url:
                raise ValueError("WebSocket connection requires a URL. Set the 'mcp_connection_url' header.")
            
            # Connect to the WebSocket server
            read_stream, write_stream = await websocket_client(self.connection_url, token=self.connection_token)
            
        elif self.connection_type == "http":
            if not HAS_REMOTE_MCP:
                raise ImportError("HTTP connection requires mcp package with HTTP support. Update your mcp package.")
            
            if not self.connection_url:
                raise ValueError("HTTP connection requires a URL. Set the 'mcp_connection_url' header.")
            
            # Connect to the HTTP server
            read_stream, write_stream = await http_client(self.connection_url, token=self.connection_token)
            
        else:  # Default to stdio
            if not self.server_command:
                raise ValueError("No MCP server command specified. Set the 'mcp_server_command' header.")
            
            # Set up server parameters
            server_params = StdioServerParameters(
                command=self.server_command,
                args=self.server_args,
                env=self.server_env,
            )
            
            # Connect to the server
            read_stream, write_stream = await stdio_client(server_params)
        
        # Create a client session
        session = ClientSession(read_stream, write_stream)
        
        # Initialize the session
        await session.initialize()
        
        return session, None

    async def _get_data_from_resource(self, session: ClientSession) -> List[Dict[str, str]]:
        """
        Retrieve data from an MCP resource.
        
        Args:
            session (ClientSession): The active MCP session
            
        Returns:
            List[Dict[str, str]]: The search results formatted for GPT Researcher
        """
        if not self.resource_uri_template:
            return []
        
        # Format the resource URI with the query if needed
        resource_uri = self.resource_uri_template
        if "{query}" in resource_uri:
            resource_uri = resource_uri.replace("{query}", self.query)
        
        try:
            # Read the resource
            content, mime_type = await session.read_resource(resource_uri)
            
            # Return the content as a search result
            return [{
                "href": resource_uri,
                "body": content
            }]
        except Exception as e:
            logger.error(f"Error reading MCP resource {resource_uri}: {e}")
            return []

    async def _get_data_from_tool(self, session: ClientSession) -> List[Dict[str, str]]:
        """
        Retrieve data by invoking an MCP tool.
        
        Args:
            session (ClientSession): The active MCP session
            
        Returns:
            List[Dict[str, str]]: The search results formatted for GPT Researcher
        """
        if not self.tool_name:
            return []
        
        try:
            # Call the tool with the provided arguments
            result = await session.call_tool(self.tool_name, self.tool_args)
            
            # Process the result based on its type
            if isinstance(result, list):
                # If the result is already a list, ensure each item has href and body
                search_results = []
                for item in result:
                    if isinstance(item, dict):
                        # Convert the item to the expected format
                        search_result = {
                            "href": item.get("url", item.get("href", f"mcp://tool/{self.tool_name}")),
                            "body": item.get("content", item.get("body", str(item)))
                        }
                        search_results.append(search_result)
                    else:
                        # Simple string or other type
                        search_results.append({
                            "href": f"mcp://tool/{self.tool_name}",
                            "body": str(item)
                        })
                return search_results
            else:
                # For a single result, return it as one item
                return [{
                    "href": f"mcp://tool/{self.tool_name}",
                    "body": str(result)
                }]
        except Exception as e:
            logger.error(f"Error calling MCP tool {self.tool_name}: {e}")
            return []

    async def _search_with_mcp(self) -> List[Dict[str, str]]:
        """
        Perform a search using an MCP server.
        
        Returns:
            List[Dict[str, str]]: The search results
        """
        try:
            # Connect to the MCP server
            session, _ = await self._connect_to_server()
            
            try:
                results = []
                
                # If a resource URI is specified, get data from the resource
                if self.resource_uri_template:
                    resource_results = await self._get_data_from_resource(session)
                    results.extend(resource_results)
                
                # If a tool is specified, get data from the tool
                if self.tool_name:
                    tool_results = await self._get_data_from_tool(session)
                    results.extend(tool_results)
                
                # If no resource or tool was specified, try to list available resources and tools
                if not results:
                    # Try to list available resources
                    try:
                        resources = await session.list_resources()
                        if resources:
                            results.append({
                                "href": "mcp://resources",
                                "body": f"Available MCP resources: {', '.join(r.name for r in resources)}"
                            })
                    except Exception as e:
                        logger.debug(f"Could not list MCP resources: {e}")
                    
                    # Try to list available tools
                    try:
                        tools = await session.list_tools()
                        if tools:
                            results.append({
                                "href": "mcp://tools",
                                "body": f"Available MCP tools: {', '.join(t.name for t in tools)}"
                            })
                    except Exception as e:
                        logger.debug(f"Could not list MCP tools: {e}")
                
                return results
            finally:
                # Ensure the session is closed properly
                await session.close()
        except Exception as e:
            logger.error(f"Error performing MCP search: {e}")
            return []

    def search(self, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Perform a search using an MCP server.
        
        Args:
            max_results (int, optional): Maximum number of results to return.
            
        Returns:
            List[Dict[str, str]]: The search results
        """
        if not HAS_MCP:
            logger.error("The MCP Python package is not installed. Install it with 'pip install mcp'.")
            return []
        
        try:
            # Run the asynchronous search function
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(self._search_with_mcp())
            
            # Limit results if needed
            return results[:max_results] if max_results > 0 else results
        except Exception as e:
            logger.error(f"Error performing MCP search: {e}")
            return [] 