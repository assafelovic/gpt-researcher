import asyncio
import logging
import json
from typing import List, Dict, Any, Optional

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain_mcp_adapters.tools import load_mcp_tools
    HAS_MCP_ADAPTERS = True
except ImportError:
    HAS_MCP_ADAPTERS = False

from ..utils import stream_output

logger = logging.getLogger(__name__)


class MCPRetriever:
    """
    Model Context Protocol (MCP) Retriever for GPT Researcher using langchain-mcp-adapters
    
    This retriever enables GPT Researcher to use MCP servers as data sources through
    LangChain tools integration. It uses the official langchain-mcp-adapters library
    for standardized MCP integration.
    
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
    """

    def __init__(
        self, 
        query: str, 
        headers: Optional[Dict[str, str]] = None,
        query_domains: Optional[List[str]] = None,
        websocket=None,
        llm_provider=None,
        **kwargs
    ):
        """
        Initialize the MCP Retriever.
        
        Args:
            query (str): The search query string.
            headers (dict, optional): Headers containing MCP configuration.
            query_domains (list, optional): List of domains to search (not used in MCP).
            websocket: WebSocket for stream logging.
            llm_provider: LLM provider (researcher instance) containing mcp_configs.
            **kwargs: Additional arguments (for compatibility).
        """
        self.query = query
        self.headers = headers or {}
        self.query_domains = query_domains or []
        self.websocket = websocket
        self.llm_provider = llm_provider
        
        # Extract mcp_configs from the researcher instance
        self.mcp_configs = self._get_mcp_configs()
        
        # Log initialization
        if self.mcp_configs:
            self._stream_log_sync(f"🔧 Initializing MCP retriever for query: {self.query}")
            self._stream_log_sync(f"🔧 Found {len(self.mcp_configs)} MCP server configurations")
        else:
            logger.error("No MCP server configurations found. The retriever will fail during search.")
            self._stream_log_sync("❌ CRITICAL: No MCP server configurations found. Please check documentation.")

    def _get_mcp_configs(self) -> List[Dict[str, Any]]:
        """
        Get MCP configurations from the researcher instance.
        
        Returns:
            List[Dict[str, Any]]: List of MCP server configurations.
        """
        if self.llm_provider and hasattr(self.llm_provider, 'mcp_configs'):
            return self.llm_provider.mcp_configs or []
        return []

    async def _stream_log(self, message: str, data: Any = None):
        """Stream a log message to the websocket if available."""
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
        logger.info(message)
        
        if self.websocket:
            try:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self._stream_log(message, data))
                    else:
                        loop.run_until_complete(self._stream_log(message, data))
                except RuntimeError:
                    logger.debug("Could not stream log: no running event loop")
            except Exception as e:
                logger.error(f"Error in sync log streaming: {e}")

    def _convert_configs_to_langchain_format(self) -> Dict[str, Dict[str, Any]]:
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
            
            # Auto-detect transport type from URL if provided
            connection_url = config.get("connection_url")
            if connection_url:
                if connection_url.startswith(("wss://", "ws://")):
                    server_config["transport"] = "websocket"
                    server_config["url"] = connection_url
                elif connection_url.startswith(("https://", "http://")):
                    server_config["transport"] = "streamable_http"
                    server_config["url"] = connection_url
                else:
                    # Fallback to specified connection_type or stdio
                    connection_type = config.get("connection_type", "stdio")
                    server_config["transport"] = connection_type
                    if connection_type in ["websocket", "streamable_http", "http"]:
                        server_config["url"] = connection_url
            else:
                # No URL provided, use stdio (default) or specified connection_type
                connection_type = config.get("connection_type", "stdio")
                server_config["transport"] = connection_type
            
            # Handle stdio transport configuration
            if server_config.get("transport") == "stdio":
                if config.get("server_command"):
                    server_config["command"] = config["server_command"]
                    
                    # Handle server_args
                    server_args = config.get("server_args", [])
                    if isinstance(server_args, str):
                        server_args = server_args.split()
                    server_config["args"] = server_args
                    
                    # Handle environment variables
                    server_env = config.get("env", {})
                    if server_env:
                        server_config["env"] = server_env
                        
            # Add authentication if provided
            if config.get("connection_token"):
                server_config["token"] = config["connection_token"]
                
            server_configs[server_name] = server_config
            
        return server_configs

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
            await self._stream_log("⚠️ LLM provider not available for tool argument generation")
            return ""
            
        try:
            await self._stream_log("🧠 Calling LLM for tool assistance")
            from gpt_researcher.utils.llm import create_chat_completion
            
            # Get LLM configuration from the researcher instance
            if hasattr(self.llm_provider, 'cfg'):
                cfg = self.llm_provider.cfg
                model = cfg.strategic_llm_model
                provider = cfg.strategic_llm_provider
            else:
                # Fallback configuration
                model = "gpt-4"
                provider = "openai"
            
            messages = [{"role": "user", "content": prompt}]
            result = await create_chat_completion(
                model=model,
                messages=messages,
                temperature=0.0,
                llm_provider=provider,
                max_tokens=None,
            )
            return result
        except Exception as e:
            logger.error(f"Error calling LLM for argument generation: {e}")
            await self._stream_log(f"❌ Error calling LLM: {str(e)}")
            return ""

    async def _generate_tool_arguments(self, tool, query: str) -> Dict[str, Any]:
        """
        Generate arguments for a LangChain tool using the LLM.
        
        Args:
            tool: The LangChain tool
            query: The search query
            
        Returns:
            Dict[str, Any]: The generated arguments
        """
        try:
            # Get tool schema
            tool_schema = tool.tool_spec if hasattr(tool, 'tool_spec') else {}
            tool_name = tool.name
            tool_description = tool.description
            
            # Generate prompt for argument generation
            prompt = f"""
Generate valid arguments for this tool based on the research query.

TOOL INFORMATION:
Name: {tool_name}
Description: {tool_description}

RESEARCH QUERY:
{query}

Based on the tool description and research query, generate appropriate arguments for this tool.
Return a JSON object where keys are parameter names and values are appropriate parameter values.

If the tool appears to be a search tool, use the research query as the search term.
If no specific parameters are obvious from the description, return an empty JSON object {{}}.
"""
            
            # Call LLM to generate arguments
            args_text = await self._call_llm(prompt)
            
            # Parse the JSON response
            try:
                args = json.loads(args_text)
            except json.JSONDecodeError:
                # Try to extract JSON from text
                import re
                json_match = re.search(r"\{.*\}", args_text, re.DOTALL)
                if json_match:
                    args = json.loads(json_match.group(0))
                else:
                    # Fallback: use common search patterns
                    args = {}
                    if any(keyword in tool_name.lower() or keyword in tool_description.lower() 
                          for keyword in ['search', 'query', 'find', 'lookup']):
                        # Try common parameter names for search tools
                        for param_name in ['query', 'q', 'search', 'input', 'text']:
                            args[param_name] = query
                            break
            
            await self._stream_log(f"✓ Generated arguments for tool '{tool_name}': {json.dumps(args)}")
            return args
            
        except Exception as e:
            logger.error(f"Error generating tool arguments: {e}")
            await self._stream_log(f"❌ Error generating arguments: {str(e)}")
            
            # Fallback: try common search parameter names
            fallback_args = {}
            if any(keyword in tool.name.lower() or keyword in tool.description.lower() 
                  for keyword in ['search', 'query', 'find', 'lookup']):
                fallback_args = {"query": query}
                
            await self._stream_log(f"⚠️ Using fallback arguments: {json.dumps(fallback_args)}")
            return fallback_args

    async def _execute_mcp_tools(self) -> List[Dict[str, str]]:
        """
        Execute MCP tools using langchain-mcp-adapters.
        
        Returns:
            List[Dict[str, str]]: The search results from MCP tools.
        """
        if not HAS_MCP_ADAPTERS:
            await self._stream_log("❌ langchain-mcp-adapters not installed")
            raise ValueError("langchain-mcp-adapters package not installed. Install with: pip install langchain-mcp-adapters")
            
        if not self.mcp_configs:
            await self._stream_log("❌ No MCP server configurations found")
            return []
            
        try:
            # Convert configs to langchain format
            server_configs = self._convert_configs_to_langchain_format()
            await self._stream_log(f"🔧 Connecting to {len(server_configs)} MCP server(s)")
            
            # Initialize the MultiServerMCPClient
            client = MultiServerMCPClient(server_configs)
            
            # Get tools from all servers
            tools = await client.get_tools()
            
            if not tools:
                await self._stream_log("⚠️ No tools available from MCP servers")
                return []
                
            await self._stream_log(f"✅ Loaded {len(tools)} MCP tools")
            
            # Execute tools and collect results
            all_results = []
            
            for tool in tools:
                try:
                    await self._stream_log(f"🔧 Executing tool: {tool.name}")
                    
                    # Generate arguments for this tool
                    args = await self._generate_tool_arguments(tool, self.query)
                    
                    # Execute the tool
                    if hasattr(tool, 'invoke'):
                        # LangChain tool interface
                        result = await tool.ainvoke(args) if hasattr(tool, 'ainvoke') else tool.invoke(args)
                    elif hasattr(tool, 'run'):
                        # Alternative tool interface
                        result = await tool.arun(args) if hasattr(tool, 'arun') else tool.run(args)
                    else:
                        # Fallback: try calling directly
                        result = tool(args)
                    
                    # Process result into search result format
                    search_results = self._process_tool_result(tool.name, result)
                    all_results.extend(search_results)
                    
                    await self._stream_log(f"✓ Tool '{tool.name}' returned {len(search_results)} results")
                    
                except Exception as e:
                    logger.error(f"Error executing tool {tool.name}: {e}")
                    await self._stream_log(f"❌ Error executing tool '{tool.name}': {str(e)}")
                    continue
            
            await self._stream_log(f"✅ Retrieved {len(all_results)} total results from all MCP tools")
            return all_results
            
        except Exception as e:
            logger.error(f"Error executing MCP tools: {e}")
            await self._stream_log(f"❌ Error executing MCP tools: {str(e)}")
            return []

    def _process_tool_result(self, tool_name: str, result: Any) -> List[Dict[str, str]]:
        """
        Process tool result into search result format.
        
        Args:
            tool_name: Name of the tool that produced the result
            result: The tool result
            
        Returns:
            List[Dict[str, str]]: Formatted search results
        """
        search_results = []
        
        try:
            if isinstance(result, list):
                # If the result is already a list, process each item
                for i, item in enumerate(result):
                    if isinstance(item, dict):
                        # Use the item as is if it has required fields
                        if "title" in item and ("content" in item or "body" in item):
                            search_result = {
                                "title": item.get("title", ""),
                                "href": item.get("href", item.get("url", f"mcp://{tool_name}/{i}")),
                                "body": item.get("body", item.get("content", str(item))),
                            }
                            search_results.append(search_result)
                        else:
                            # Create a search result with a generic title
                            search_result = {
                                "title": f"Result from {tool_name}",
                                "href": f"mcp://{tool_name}/{i}",
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
                
        except Exception as e:
            logger.error(f"Error processing tool result from {tool_name}: {e}")
            # Fallback: create a basic result
            search_result = {
                "title": f"Result from {tool_name}",
                "href": f"mcp://{tool_name}",
                "body": str(result),
            }
            search_results.append(search_result)
        
        return search_results

    def search(self, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Perform a search using MCP tools via langchain-mcp-adapters.
        
        Args:
            max_results: Maximum number of results to return.
            
        Returns:
            List[Dict[str, str]]: The search results.
            
        Raises:
            ValueError: If no MCP server configurations are available.
        """
        # Check if we have any server configurations
        if not self.mcp_configs:
            error_msg = "No MCP server configurations available. Please provide mcp_configs parameter to GPTResearcher."
            logger.error(error_msg)
            self._stream_log_sync("❌ MCP retriever cannot proceed without server configurations.")
            raise ValueError(error_msg)
            
        # Log to help debug the integration flow
        logger.info(f"MCPRetriever.search called for query: {self.query}")
            
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create a new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        try:
            # Run the MCP search using langchain-mcp-adapters
            results = loop.run_until_complete(self._execute_mcp_tools())
            
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