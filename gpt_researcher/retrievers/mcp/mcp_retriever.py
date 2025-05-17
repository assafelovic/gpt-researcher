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
       
    Multiple MCP servers:
    
    The retriever supports connecting to multiple MCP servers in parallel. When
    multiple server configurations are provided, the retriever queries all servers
    and combines their results.
    
    Server configurations are expected in headers as follows:
    - Single server: mcp_server_command, mcp_server_args, etc.
    - Multiple servers: mcp1_server_command, mcp1_server_args, mcp2_server_command, etc.
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
            headers (dict, optional): Headers for general configuration, not used for MCP configuration anymore.
            query_domains (list, optional): List of domains to search (not directly used in MCP).
            server_name (str, optional): Name of the MCP server to connect to.
            server_command (str, optional): Command to start the MCP server.
            server_args (list, optional): Arguments to pass to the server command.
            server_env (dict, optional): Environment variables for the server.
            resource_uri_template (str, optional): URI template for accessing a resource.
            tool_name (str, optional): Name of the MCP tool to invoke.
            connection_type (str, optional): Type of connection (stdio, websocket, http).
            connection_url (str, optional): URL for WebSocket or HTTP connection.
            connection_token (str, optional): Authentication token for remote connections.
            llm_provider (object, optional): LLM provider for generating arguments.
            websocket: WebSocket for stream logging.
        
        Note:
            Tool arguments are dynamically generated for each MCP tool call
            based on the query context using the LLM provider.
            
            For multiple MCP servers, use the `mcp_configs` parameter in GPTResearcher
            instead of this direct constructor.
            
            Headers-based configuration is no longer supported.
        """
        self.query = query
        self.headers = headers or {}
        self.query_domains = query_domains or []
        self.websocket = websocket
        
        # Extract websocket from headers if available
        if self.headers.get("websocket") and not self.websocket:
            self.websocket = self.headers.get("websocket")
            
        # Configure LLM-based argument generation and tool selection
        self.use_auto_tool_selection = os.getenv("MCP_AUTO_TOOL_SELECTION", "false").lower() in ["true", "1", "yes"]
        self.llm_provider = llm_provider
        
        # Store constructor parameters for later use in _discover_server_configs
        self.constructor_params = {
            "server_name": server_name,
            "server_command": server_command,
            "server_args": server_args,
            "server_env": server_env,
            "resource_uri_template": resource_uri_template,
            "tool_name": tool_name,
            "connection_type": connection_type,
            "connection_url": connection_url,
            "connection_token": connection_token,
        }
        
        # Check if any deprecated header-based MCP configuration is present
        if any(key.startswith("mcp_") or key.startswith("mcp1_") for key in self.headers):
            logger.warning("MCP configuration via headers is deprecated and no longer supported. Use mcp_configs parameter instead.")
            self._stream_log_sync("⚠️ MCP configuration via headers is deprecated and will be ignored. Please use the mcp_configs parameter instead.")
        
        # Discover server configurations (constructor parameters only)
        self.server_configs = self._discover_server_configs()
        
        # Log initialization
        if self.server_configs:
            self._stream_log_sync(f"🔧 Initializing MCP retriever for query: {self.query}")
            self._stream_log_sync(f"🔧 Found {len(self.server_configs)} MCP server configurations")
            
            for i, config in enumerate(self.server_configs):
                if config.get("server_command"):
                    self._stream_log_sync(f"🔧 MCP server {i+1}: {config['server_command']} {' '.join(config.get('server_args', []))}")
                elif config.get("connection_url"):
                    self._stream_log_sync(f"🔧 MCP server {i+1}: {config['connection_url']} (via {config.get('connection_type', 'stdio')})")
            
            if self.use_auto_tool_selection:
                self._stream_log_sync("🔍 Auto tool selection is enabled")
        else:
            logger.error("No MCP server configurations found. The retriever will fail during search.")
            self._stream_log_sync("❌ CRITICAL: No MCP server configurations found. The research process will fail. Please check documentation at https://docs.gptr.dev/gpt-researcher/retrievers/mcp-configs for proper configuration.")

    def _discover_server_configs(self) -> List[Dict[str, Any]]:
        """
        Get MCP server configurations.
        
        This method only uses the constructor parameters provided via mcp_configs.
        Header-based configuration is no longer supported.
        
        Returns:
            List[Dict[str, Any]]: List of server configuration dictionaries.
        """
        configs = []
        
        # Only use constructor parameters, headers are no longer supported
        if self.constructor_params:
            # Filter out None values
            params = {k: v for k, v in self.constructor_params.items() if v is not None}
            
            # Check if we have either server_command or connection_url
            if params.get("server_command") or params.get("connection_url"):
                config = self._create_server_config(params)
                if config:
                    configs.append(config)
        
        # If no configs found, log a helpful message for the user
        if not configs:
            logger.warning("No MCP server configurations found. Please provide proper mcp_configs.")
            try:
                self._stream_log_sync("⚠️ No MCP server configurations found. Headers-based configuration is no longer supported. Please provide proper mcp_configs parameter. See documentation at https://docs.gptr.dev/gpt-researcher/retrievers/mcp-configs")
            except Exception as e:
                logger.error(f"Error streaming log: {e}")
        
        return configs

    def _create_server_config(self, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Create a server configuration from parameters.
        
        Args:
            params: Dictionary of parameter key-value pairs.
            
        Returns:
            Dict[str, Any]: Server configuration, or None if invalid.
        """
        # Skip if no server command or connection URL
        if not params.get("server_command") and not params.get("connection_url"):
            return None
            
        config = {}
        
        # Process standard parameters
        for key, value in params.items():
            # Skip env parameters, will handle separately
            if key.startswith("env_"):
                continue
                
            # Handle server_args as a list
            if key == "server_args":
                config[key] = value.split() if isinstance(value, str) else value
            else:
                config[key] = value
        
        # Process environment variables
        server_env = {}
        for key, value in params.items():
            if key.startswith("env_"):
                env_name = key[4:]  # Remove 'env_' prefix
                server_env[env_name] = value
                
        if server_env:
            config["server_env"] = server_env
            
        # Auto-detect connection type from URL if not explicitly set
        if config.get("connection_url") and not config.get("connection_type"):
            url = config["connection_url"]
            if url.startswith(("ws://", "wss://")):
                config["connection_type"] = "websocket"
            elif url.startswith(("http://", "https://")):
                config["connection_type"] = "http"
                
        return config

    async def _stream_log(self, message: str, data: Any = None):
        """Stream a log message to the websocket if available."""
        # Log to logger regardless of websocket
        logger.info(message)
        
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
                
    def _stream_log_sync(self, message: str, data: Any = None):
        """Synchronous version of _stream_log for use in sync contexts."""
        # Log to logger regardless of websocket
        logger.info(message)
        
        if self.websocket:
            try:
                # Try to run in event loop if one exists
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Schedule the coroutine to run in the event loop
                        asyncio.create_task(self._stream_log(message, data))
                    else:
                        # Run the coroutine directly in the loop
                        loop.run_until_complete(self._stream_log(message, data))
                except RuntimeError:
                    # If no event loop exists or it's closed, just log and move on
                    logger.debug("Could not stream log: no running event loop")
            except Exception as e:
                logger.error(f"Error in sync log streaming: {e}")

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

            # If there's only one tool, use it
            if len(tools) == 1:
                await self._stream_log(f"✓ Using the only available tool: {tools[0].name}")
                return tools[0]
                
            # Format tool descriptions for LLM
            tool_descriptions = "\n".join([
                f"Tool: {tool.name}\n"
                f"Description: {tool.description}\n"
                f"Arguments: {', '.join([param.name + (' (required)' if param.required else '') for param in tool.parameters])}\n"
                for tool in tools
            ])
            
            # Generate prompt for tool selection
            prompt = f"""
Given the following MCP tools and a research query, select the most appropriate tool for obtaining relevant information.

AVAILABLE TOOLS:
{tool_descriptions}

RESEARCH QUERY:
{query}

Return only the name of the single most appropriate tool (exactly as written above) and nothing else.
"""
            # Call LLM to select the best tool
            tool_name = await self._call_llm(prompt)
            tool_name = tool_name.strip()
            
            # Find the selected tool
            selected_tool = next((tool for tool in tools if tool.name == tool_name), None)
            
            if selected_tool:
                await self._stream_log(f"✓ Selected tool: {selected_tool.name}")
                return selected_tool
            else:
                # Fallback to the first tool if LLM selection failed
                await self._stream_log(f"⚠️ Could not find tool '{tool_name}', using first available tool: {tools[0].name}")
                return tools[0]
                
        except Exception as e:
            logger.error(f"Error selecting MCP tool: {e}")
            await self._stream_log(f"❌ Error selecting tool: {str(e)}")
            return None

    async def _generate_tool_arguments(self, tool: Any, query: str) -> Dict[str, Any]:
        """
        Generate arguments for an MCP tool using the LLM.
        
        Args:
            tool: The MCP tool definition.
            query: The search query.
            
        Returns:
            Dict[str, Any]: The generated arguments.
        """
        try:
            # Format parameter descriptions for LLM
            param_descriptions = "\n".join([
                f"- {param.name}: {param.description} (Type: {param.type}, Required: {param.required}, Default: {getattr(param, 'default', 'None')})"
                for param in tool.parameters
            ])
            
            # Generate prompt for argument generation
            prompt = f"""
Generate valid arguments for an MCP tool based on the research query and tool definition.

TOOL INFORMATION:
Name: {tool.name}
Description: {tool.description}

PARAMETERS:
{param_descriptions}

RESEARCH QUERY:
{query}

Generate appropriate values for all required parameters and any optional parameters that would help the tool provide useful results.
Return a JSON object where keys are parameter names and values are appropriate parameter values.
Only include parameters that are defined for this tool.
"""
            # Call LLM to generate arguments
            args_text = await self._call_llm(prompt)
            
            # Parse the JSON response
            try:
                args = json.loads(args_text)
            except json.JSONDecodeError:
                # Try to extract JSON from text
                import re
                json_match = re.search(r"{.*}", args_text, re.DOTALL)
                if json_match:
                    args = json.loads(json_match.group(0))
                else:
                    await self._stream_log("⚠️ Failed to parse LLM-generated arguments as JSON, using empty arguments")
                    args = {}
            
            # Validate arguments against tool parameters
            valid_args = {}
            for param in tool.parameters:
                if param.name in args:
                    valid_args[param.name] = args[param.name]
                elif param.required:
                    # For required parameters, use a reasonable default based on the query
                    if param.type == "string" and param.name.lower() in ["query", "search", "q", "input", "text"]:
                        valid_args[param.name] = query
                    elif param.type == "integer" and param.name.lower() in ["max_results", "limit", "count"]:
                        valid_args[param.name] = 10
                    else:
                        await self._stream_log(f"⚠️ Missing required parameter '{param.name}' for tool '{tool.name}'")
            
            await self._stream_log(f"✓ Generated arguments for tool '{tool.name}': {json.dumps(valid_args)}")
            return valid_args
            
        except Exception as e:
            logger.error(f"Error generating tool arguments: {e}")
            await self._stream_log(f"❌ Error generating arguments: {str(e)}")
            
            # Fallback: use query for anything that looks like a query parameter
            fallback_args = {}
            for param in tool.parameters:
                if param.required and param.type == "string" and param.name.lower() in ["query", "search", "q", "input", "text"]:
                    fallback_args[param.name] = query
                elif param.required and param.type == "integer" and param.name.lower() in ["max_results", "limit", "count"]:
                    fallback_args[param.name] = 10
            
            await self._stream_log(f"⚠️ Using fallback arguments: {json.dumps(fallback_args)}")
            return fallback_args

    async def _connect_to_server(self, server_config: Dict[str, Any]) -> Tuple[Optional[ClientSession], Any]:
        """
        Connect to an MCP server using the specified configuration.
        
        Args:
            server_config: Server configuration dictionary.
            
        Returns:
            Tuple[Optional[ClientSession], Any]: The MCP session and server details, or (None, None) on failure.
        """
        try:
            connection_type = server_config.get("connection_type", "stdio")
            
            if connection_type == "websocket":
                connection_url = server_config.get("connection_url")
                if not connection_url:
                    await self._stream_log("❌ Missing WebSocket URL")
                    return None, None
                    
                await self._stream_log(f"🔌 Connecting to MCP server via WebSocket: {connection_url}")
                
                # Connect using WebSocket
                headers = {}
                if token := server_config.get("connection_token"):
                    headers["Authorization"] = f"Bearer {token}"
                    
                read, write, _ = await websocket_client(connection_url, headers=headers)
                session = ClientSession(read, write)
                await session.initialize()
                
                return session, {"connection_type": "websocket", "url": connection_url}
                
            elif connection_type == "http":
                connection_url = server_config.get("connection_url")
                if not connection_url:
                    await self._stream_log("❌ Missing HTTP URL")
                    return None, None
                    
                await self._stream_log(f"🔌 Connecting to MCP server via HTTP: {connection_url}")
                
                # Connect using HTTP
                headers = {}
                if token := server_config.get("connection_token"):
                    headers["Authorization"] = f"Bearer {token}"
                    
                read, write, _ = await http_client(connection_url, headers=headers)
                session = ClientSession(read, write)
                await session.initialize()
                
                return session, {"connection_type": "http", "url": connection_url}
                
            else:  # Default to stdio
                server_command = server_config.get("server_command")
                server_args = server_config.get("server_args", [])
                server_env = server_config.get("server_env", {})
                
                if not server_command:
                    await self._stream_log("❌ Missing server command")
                    return None, None
                    
                await self._stream_log(f"🔌 Starting MCP server: {server_command} {' '.join(server_args)}")
                
                # Create server parameters
                server_params = StdioServerParameters(
                    command=server_command,
                    args=server_args,
                    env=server_env,
                )
                
                # Connect using stdio
                read, write = await stdio_client(server_params)
                session = ClientSession(read, write)
                await session.initialize()
                
                return session, {"connection_type": "stdio", "command": server_command, "args": server_args}
                
        except Exception as e:
            logger.error(f"Error connecting to MCP server: {e}")
            await self._stream_log(f"❌ Error connecting to MCP server: {str(e)}")
            return None, None

    async def _get_data_from_resource(self, session: ClientSession, server_config: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Get data from an MCP resource.
        
        Args:
            session: The MCP client session.
            server_config: Server configuration dictionary.
            
        Returns:
            List[Dict[str, str]]: The retrieved data formatted as search results.
        """
        try:
            resource_uri = server_config.get("resource_uri_template", "").format(query=self.query)
            if not resource_uri:
                await self._stream_log("⚠️ No resource URI template specified")
                return []
                
            await self._stream_log(f"📂 Reading resource: {resource_uri}")
            
            content, mime_type = await session.read_resource(resource_uri)
            
            # Create a search result format
            result = [{
                "title": f"Resource: {resource_uri}",
                "href": resource_uri,
                "body": content[:1000] + ("..." if len(content) > 1000 else ""),
                "content": content,
                "mime_type": mime_type
            }]
            
            await self._stream_log(f"✓ Retrieved resource: {len(content)} characters, mime type: {mime_type}")
            return result
            
        except Exception as e:
            logger.error(f"Error reading MCP resource: {e}")
            await self._stream_log(f"❌ Error reading resource: {str(e)}")
            return []

    async def _get_data_from_tool(self, session: ClientSession, server_config: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Get data from an MCP tool.
        
        Args:
            session: The MCP client session.
            server_config: Server configuration dictionary.
            
        Returns:
            List[Dict[str, str]]: The retrieved data formatted as search results.
        """
        try:
            # Get tool name from config or auto-select
            tool_name = server_config.get("tool_name")
            selected_tool = None
            
            if tool_name:
                # Get the tool by name
                tools = await session.list_tools()
                selected_tool = next((t for t in tools if t.name == tool_name), None)
                
                if not selected_tool:
                    await self._stream_log(f"❌ Tool '{tool_name}' not found on the server")
                    available_tools = [t.name for t in tools]
                    await self._stream_log(f"Available tools: {', '.join(available_tools) if available_tools else 'none'}")
                    return []
            else:
                # Auto-select the best tool
                selected_tool = await self._select_best_mcp_tool(session, self.query)
                
                if not selected_tool:
                    await self._stream_log("❌ No suitable tool found on the server")
                    return []
                    
                tool_name = selected_tool.name
            
            # Generate arguments for the tool
            args = await self._generate_tool_arguments(selected_tool, self.query)
            
            # Call the tool
            await self._stream_log(f"🔧 Calling tool: {tool_name} with arguments: {json.dumps(args)}")
            result = await session.call_tool(tool_name, args)
            
            # Process the result based on its type
            search_results = []
            
            if isinstance(result, list):
                # If the result is already a list, process each item
                for item in result:
                    if isinstance(item, dict):
                        # Use the item as is if it has required fields
                        if "title" in item and ("content" in item or "body" in item):
                            search_result = {
                                "title": item.get("title", ""),
                                "href": item.get("href", item.get("url", f"mcp://{tool_name}/{hash(str(item))}")),
                                "body": item.get("body", item.get("content", str(item))),
                            }
                            search_results.append(search_result)
                        else:
                            # Create a search result with a generic title
                            search_result = {
                                "title": f"Result from {tool_name}",
                                "href": f"mcp://{tool_name}/{hash(str(item))}",
                                "body": str(item),
                            }
                            search_results.append(search_result)
            elif isinstance(result, dict):
                # If the result is a dictionary, use it as a single search result
                search_result = {
                    "title": result.get("title", f"Result from {tool_name}"),
                    "href": result.get("href", result.get("url", f"mcp://{tool_name}")),
                    "body": result.get("body", result.get("content", str(result))),
                }
                search_results.append(search_result)
            else:
                # For any other type, convert to string and use as a single search result
                search_result = {
                    "title": f"Result from {tool_name}",
                    "href": f"mcp://{tool_name}",
                    "body": str(result),
                }
                search_results.append(search_result)
            
            await self._stream_log(f"✓ Retrieved {len(search_results)} results from tool: {tool_name}")
            return search_results
            
        except Exception as e:
            logger.error(f"Error calling MCP tool: {e}")
            await self._stream_log(f"❌ Error calling tool: {str(e)}")
            return []

    async def _search_with_mcp(self) -> List[Dict[str, str]]:
        """
        Search using MCP servers.
        
        Returns:
            List[Dict[str, str]]: The search results from all MCP servers.
        """
        if not self.server_configs:
            await self._stream_log("❌ No MCP server configurations found")
            return []
            
        all_results = []
        
        # Process each server configuration in parallel
        tasks = []
        
        for server_config in self.server_configs:
            task = asyncio.create_task(self._search_with_server(server_config))
            tasks.append(task)
            
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Error in MCP search: {result}")
                await self._stream_log(f"❌ Error in MCP search: {str(result)}")
                
        await self._stream_log(f"✓ Retrieved {len(all_results)} total results from all MCP servers")
        return all_results

    async def _search_with_server(self, server_config: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Search using a single MCP server.
        
        Args:
            server_config: Server configuration dictionary.
            
        Returns:
            List[Dict[str, str]]: The search results from this server.
        """
        session, server_details = await self._connect_to_server(server_config)
        
        if not session:
            return []
            
        try:
            # Log server connection
            server_name = server_config.get("server_name", "MCP Server")
            if server_details.get("connection_type") == "stdio":
                await self._stream_log(f"✓ Connected to {server_name} via stdio: {server_details.get('command')}")
            else:
                await self._stream_log(f"✓ Connected to {server_name} via {server_details.get('connection_type')}: {server_details.get('url')}")
            
            results = []
            
            # Try to get data from a resource if configured
            if server_config.get("resource_uri_template"):
                resource_results = await self._get_data_from_resource(session, server_config)
                results.extend(resource_results)
                
            # Try to get data from a tool
            tool_results = await self._get_data_from_tool(session, server_config)
            results.extend(tool_results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching with MCP server: {e}")
            await self._stream_log(f"❌ Error searching with MCP server: {str(e)}")
            return []
            
        finally:
            # Close the session
            if session:
                await session.close()

    def search(self, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Perform a search using MCP.
        
        Args:
            max_results: Maximum number of results to return.
            
        Returns:
            List[Dict[str, str]]: The search results.
            
        Raises:
            ValueError: If no MCP server configurations are available.
        """
        # Check if we have any server configurations
        if not self.server_configs:
            error_msg = "No MCP server configurations available. Please provide proper MCP configuration."
            logger.error(error_msg)
            self._stream_log_sync("❌ MCP retriever cannot proceed without server configurations. Please check the documentation at https://docs.gptr.dev/gpt-researcher/retrievers/mcp-configs")
            
            # Raise an exception to stop the process
            raise ValueError(error_msg + " See documentation at https://docs.gptr.dev/gpt-researcher/retrievers/mcp-configs")
            
        # Log to help debug the integration flow
        logger.info(f"MCPRetriever.search called for query: {self.query}")
            
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create a new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        try:
            # Run the MCP search
            results = loop.run_until_complete(self._search_with_mcp())
            
            # Limit the number of results
            if len(results) > max_results:
                logger.info(f"Limiting {len(results)} MCP results to {max_results}")
                results = results[:max_results]
            
            # Log result summary    
            logger.info(f"MCPRetriever returning {len(results)} results")
                
            return results
            
        except Exception as e:
            logger.error(f"Error in MCP search: {e}")
            self._stream_log_sync(f"❌ Error in MCP search: {str(e)}")
            # Raise the exception to stop the process
            raise ValueError(f"MCP search failed: {str(e)}") 