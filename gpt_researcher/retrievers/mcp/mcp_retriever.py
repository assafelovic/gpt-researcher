import asyncio
import logging
import os
import json
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

from ..utils import stream_output

logger = logging.getLogger(__name__)

class MCPRetriever:
    """
    Model Context Protocol (MCP) Retriever for GPT Researcher
    
    This retriever enables GPT Researcher to use MCP servers as data sources.
    MCP servers provide standardized access to tools, resources, and prompts.
    
    The retriever can connect to any MCP server that follows the protocol spec,
    including local servers and remote servers via WebSocket or HTTP.
    
    Usage scenarios:
    
    1. Standalone retriever:
       When "mcp" is the only retriever specified, it fully replaces web search.
       All research context comes from MCP servers.
    
    2. Multi-retriever mode:
       When "mcp" is specified alongside other retrievers (e.g., "mcp,tavily"),
       both retrievers run in parallel, and their results are combined.
       
    In either case, the MCP server and tool configuration must be explicitly
    provided via headers or environment variables. There is no default MCP
    server configuration.
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
        llm_provider=None,
        websocket=None,
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
            llm_provider (object, optional): LLM provider for generating arguments.
            websocket: WebSocket for stream logging.
        """
        self.query = query
        self.headers = headers or {}
        self.query_domains = query_domains or []
        self.websocket = websocket
        
        # Extract websocket from headers if available
        if self.headers.get("websocket") and not self.websocket:
            self.websocket = self.headers.get("websocket")
        
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
            self._stream_log("🔌 MCP package not installed. Install with 'pip install mcp'.")
        # Check if remote MCP support is available
        elif self.connection_type in ["websocket", "http"] and not HAS_REMOTE_MCP:
            logger.warning(
                f"The MCP Python package does not support {self.connection_type} connections. "
                "Make sure you have the latest version installed."
            )
            self._stream_log(f"🔌 MCP package doesn't support {self.connection_type} connections. Update your MCP package.")
            
        # Configure LLM-based argument generation and tool selection
        self.use_auto_tool_selection = os.getenv("MCP_AUTO_TOOL_SELECTION", "false").lower() in ["true", "1", "yes"]
        self.use_llm_args = os.getenv("MCP_USE_LLM_ARGS", "true").lower() in ["true", "1", "yes"]
        self.llm_provider = llm_provider
        
        # If llm_provider is not provided, try to get it from the global config
        if self.use_llm_args and not self.llm_provider:
            try:
                from gpt_researcher.config import Config
                cfg = Config()
                from gpt_researcher.llm_provider import GenericLLMProvider
                self.llm_provider = GenericLLMProvider(cfg)
            except Exception as e:
                logger.warning(f"Failed to initialize LLM provider for argument generation: {e}")
                self.use_llm_args = False
        
        # Log initialization
        self._stream_log(f"🔧 Initializing MCP retriever for query: {self.query}")
        if self.server_command:
            self._stream_log(f"🔧 MCP server command: {self.server_command} {' '.join(self.server_args)}")
        elif self.connection_url:
            self._stream_log(f"🔧 MCP server URL: {self.connection_url} (via {self.connection_type})")
        
        if self.use_auto_tool_selection:
            self._stream_log("🔍 Auto tool selection is enabled")
        if self.tool_name:
            self._stream_log(f"🔧 Configured to use tool: {self.tool_name}")

    async def _stream_log(self, message: str, data: Any = None):
        """Stream a log message to the websocket if available."""
        if self.websocket:
            try:
                await stream_output(
                    "logs", 
                    "mcp_retriever", 
                    message, 
                    self.websocket,
                    with_data=bool(data),
                    data=data
                )
            except Exception as e:
                logger.error(f"Error streaming log: {e}")
        logger.info(message)

    async def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM provider to generate text.
        
        Args:
            prompt (str): The prompt to send to the LLM.
            
        Returns:
            str: The generated text response.
        """
        if not self.llm_provider:
            logger.warning("LLM provider not available for argument generation")
            await self._stream_log("⚠️ LLM provider not available for tool selection/argument generation")
            return ""
            
        try:
            await self._stream_log("🧠 Calling LLM for assistance")
            from gpt_researcher.utils.llm import create_chat_completion
            
            messages = [{"role": "user", "content": prompt}]
            result = await create_chat_completion(
                model=self.llm_provider.cfg.strategic_llm_model,
                messages=messages,
                temperature=0.0,  # Use low temperature for deterministic outputs
                llm_provider=self.llm_provider.cfg.strategic_llm_provider,
                max_tokens=None,
            )
            return result
        except Exception as e:
            logger.error(f"Error calling LLM for argument generation: {e}")
            await self._stream_log(f"❌ Error calling LLM: {str(e)}")
            return ""

    async def _select_best_mcp_tool(self, session: ClientSession, query: str) -> Optional[Any]:
        """
        Intelligently select the most appropriate MCP tool for the given query.
        
        Args:
            session (ClientSession): The active MCP session.
            query (str): The search query.
            
        Returns:
            Optional[Any]: The selected tool definition, or None if no suitable tool found.
        """
        if not self.use_auto_tool_selection:
            return None
            
        try:
            # Get all available tools
            await self._stream_log("🔍 Getting available MCP tools")
            tools = await session.list_tools()
            
            if not tools:
                logger.warning("No tools available on the MCP server")
                await self._stream_log("⚠️ No tools available on the MCP server")
                return None
                
            # Log available tools
            tool_names = [t.name for t in tools]
            await self._stream_log(f"🔍 Found {len(tools)} available tools", tool_names)
                
            if len(tools) == 1:
                # If only one tool is available, use it
                await self._stream_log(f"🔧 Auto-selected the only available tool: {tools[0].name}")
                return tools[0]
                
            # Use LLM to select the most appropriate tool
            tool_descriptions = "\n".join([
                f"- {t.name}: {getattr(t, 'description', 'No description')}" 
                for t in tools
            ])
            
            prompt = f"""
You are helping to select the most appropriate tool to answer a research query.

Query: {query}

Available MCP tools:
{tool_descriptions}

Which ONE tool would be most appropriate to use for this query? 
Return only the exact tool name with no additional text or explanation.
"""
            
            await self._stream_log("🧠 Using LLM to select the best tool for the query")
            response = await self._call_llm(prompt)
            selected_tool_name = response.strip()
            
            # Find the tool in the available tools
            tool = next((t for t in tools if t.name == selected_tool_name), None)
            
            if tool:
                logger.info(f"Auto-selected MCP tool: {tool.name}")
                await self._stream_log(f"✅ Auto-selected tool: {tool.name}")
                return tool
            else:
                # If no matching tool found, use the first one
                logger.warning(f"Could not find tool '{selected_tool_name}', using first available tool")
                await self._stream_log(f"⚠️ Could not find tool '{selected_tool_name}', using {tools[0].name} instead")
                return tools[0]
                
        except Exception as e:
            logger.error(f"Error selecting MCP tool: {e}")
            await self._stream_log(f"❌ Error selecting MCP tool: {str(e)}")
            return None

    async def _generate_tool_arguments(self, tool: Any, query: str) -> Dict[str, Any]:
        """
        Generate appropriate arguments for an MCP tool using LLM.
        
        Args:
            tool: The tool definition from the MCP server.
            query (str): The search query.
            
        Returns:
            Dict[str, Any]: Generated arguments for the tool.
        """
        if not self.use_llm_args or not tool:
            return self.tool_args
            
        try:
            # Extract parameter information from the tool
            parameters = getattr(tool, "parameters", [])
            
            if not parameters:
                # If no parameters defined, use default args
                await self._stream_log(f"ℹ️ Tool {tool.name} has no parameters, using default arguments")
                return self.tool_args
                
            # Create parameter information string
            param_info = "\n".join([
                f"- {p.name} ({getattr(p, 'type', 'string')}): {getattr(p, 'description', 'No description')}" 
                for p in parameters
            ])
            
            param_names = [p.name for p in parameters]
            await self._stream_log(f"🔍 Generating arguments for {len(parameters)} parameters", param_names)
            
            # Create prompt for LLM
            prompt = f"""
You are generating arguments for an MCP tool that will be used to answer a research query.

Query: {query}

Tool: {tool.name}
Tool Description: {getattr(tool, 'description', 'No description')}

Parameters:
{param_info}

Generate appropriate values for these parameters to best answer the query.
Return ONLY a valid JSON object with parameter names and values, nothing else.
"""
            
            # Call LLM to generate arguments
            response = await self._call_llm(prompt)
            
            try:
                # Parse the JSON response
                generated_args = json.loads(response)
                
                # Merge with existing arguments, prioritizing explicitly provided args
                merged_args = {**generated_args, **self.tool_args}
                
                logger.info(f"Generated arguments for tool {tool.name}: {merged_args}")
                await self._stream_log(f"✅ Generated arguments for tool {tool.name}", merged_args)
                return merged_args
            except Exception as e:
                logger.warning(f"Failed to parse LLM-generated arguments: {e}. Using default arguments.")
                await self._stream_log(f"⚠️ Failed to parse LLM-generated arguments: {e}. Using default arguments.")
                return self.tool_args
                
        except Exception as e:
            logger.error(f"Error generating arguments: {e}")
            await self._stream_log(f"❌ Error generating arguments: {str(e)}")
            return self.tool_args

    async def _connect_to_server(self) -> Tuple[ClientSession, Any]:
        """
        Connect to an MCP server and return a session.
        
        Returns:
            Tuple[ClientSession, Any]: The MCP client session and additional context
        """
        if not HAS_MCP:
            raise ImportError("The MCP Python package is not installed. Install it with 'pip install mcp'.")
        
        await self._stream_log(f"🔌 Connecting to MCP server via {self.connection_type}")
        
        # Use the appropriate connection method based on connection_type
        if self.connection_type == "websocket":
            if not HAS_REMOTE_MCP:
                raise ImportError("WebSocket connection requires mcp package with websocket support. Update your mcp package.")
            
            if not self.connection_url:
                raise ValueError("WebSocket connection requires a URL. Set the 'mcp_connection_url' header.")
            
            # Connect to the WebSocket server
            await self._stream_log(f"🔌 Connecting to WebSocket server at {self.connection_url}")
            read_stream, write_stream = await websocket_client(self.connection_url, token=self.connection_token)
            
        elif self.connection_type == "http":
            if not HAS_REMOTE_MCP:
                raise ImportError("HTTP connection requires mcp package with HTTP support. Update your mcp package.")
            
            if not self.connection_url:
                raise ValueError("HTTP connection requires a URL. Set the 'mcp_connection_url' header.")
            
            # Connect to the HTTP server
            await self._stream_log(f"🔌 Connecting to HTTP server at {self.connection_url}")
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
            await self._stream_log(f"🔌 Starting MCP server process: {self.server_command} {' '.join(self.server_args)}")
            read_stream, write_stream = await stdio_client(server_params)
        
        # Create a client session
        session = ClientSession(read_stream, write_stream)
        
        # Initialize the session
        await self._stream_log("🔌 Initializing MCP session")
        await session.initialize()
        await self._stream_log("✅ MCP session initialized successfully")
        
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
            await self._stream_log(f"📚 Reading resource from {resource_uri}")
            content, mime_type = await session.read_resource(resource_uri)
            await self._stream_log(f"✅ Retrieved resource ({mime_type}, {len(content)} bytes)")
            
            # Return the content as a search result
            return [{
                "href": resource_uri,
                "body": content
            }]
        except Exception as e:
            logger.error(f"Error reading MCP resource {resource_uri}: {e}")
            await self._stream_log(f"❌ Error reading MCP resource {resource_uri}: {str(e)}")
            return []

    async def _get_data_from_tool(self, session: ClientSession) -> List[Dict[str, str]]:
        """
        Retrieve data by invoking an MCP tool.
        
        Args:
            session (ClientSession): The active MCP session
            
        Returns:
            List[Dict[str, str]]: The search results formatted for GPT Researcher
        """
        try:
            # If auto tool selection is enabled, select the best tool
            selected_tool = None
            if self.use_auto_tool_selection:
                selected_tool = await self._select_best_mcp_tool(session, self.query)
                if selected_tool:
                    self.tool_name = selected_tool.name
                
            # If no tool name is available, can't proceed
            if not self.tool_name:
                logger.error("No tool name specified and auto tool selection failed")
                await self._stream_log("❌ No tool name specified and auto tool selection failed")
                return []
                
            # Get tool definition if we don't already have it
            if not selected_tool:
                await self._stream_log(f"🔍 Looking for tool: {self.tool_name}")
                tools = await session.list_tools()
                selected_tool = next((t for t in tools if t.name == self.tool_name), None)
                
                if selected_tool:
                    await self._stream_log(f"✅ Found tool: {self.tool_name}")
                else:
                    await self._stream_log(f"❌ Tool not found: {self.tool_name}")
                    return []
                
            # Generate arguments for the tool
            args = await self._generate_tool_arguments(selected_tool, self.query)
            
            # Call the tool with the generated/provided arguments
            await self._stream_log(f"🧰 Calling tool: {self.tool_name}", args)
            result = await session.call_tool(self.tool_name, args)
            
            # Log the result type
            if isinstance(result, list):
                await self._stream_log(f"✅ Tool returned {len(result)} results")
            else:
                await self._stream_log(f"✅ Tool returned a single result")
            
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
            await self._stream_log(f"❌ Error calling MCP tool {self.tool_name}: {str(e)}")
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
                    await self._stream_log(f"📚 Retrieving resource using template: {self.resource_uri_template}")
                    resource_results = await self._get_data_from_resource(session)
                    results.extend(resource_results)
                
                # Get data from tool (with auto-selection if enabled)
                tool_results = await self._get_data_from_tool(session)
                results.extend(tool_results)
                
                # If no results were found, try to list available resources and tools
                if not results:
                    await self._stream_log("⚠️ No results found, listing available resources and tools")
                    
                    # Try to list available resources
                    try:
                        resources = await session.list_resources()
                        if resources:
                            resource_names = [r.name for r in resources]
                            await self._stream_log(f"📚 Available MCP resources: {len(resources)}", resource_names)
                            results.append({
                                "href": "mcp://resources",
                                "body": f"Available MCP resources: {', '.join(resource_names)}"
                            })
                    except Exception as e:
                        logger.debug(f"Could not list MCP resources: {e}")
                    
                    # Try to list available tools
                    try:
                        tools = await session.list_tools()
                        if tools:
                            tool_names = [t.name for t in tools]
                            await self._stream_log(f"🧰 Available MCP tools: {len(tools)}", tool_names)
                            results.append({
                                "href": "mcp://tools",
                                "body": f"Available MCP tools: {', '.join(tool_names)}"
                            })
                    except Exception as e:
                        logger.debug(f"Could not list MCP tools: {e}")
                
                await self._stream_log(f"✅ MCP search completed, found {len(results)} results")
                return results
            finally:
                # Ensure the session is closed properly
                await self._stream_log("🔌 Closing MCP session")
                await session.close()
        except Exception as e:
            logger.error(f"Error performing MCP search: {e}")
            await self._stream_log(f"❌ Error performing MCP search: {str(e)}")
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