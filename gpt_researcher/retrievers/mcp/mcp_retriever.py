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
    
    This retriever implements a two-stage approach:
    1. Tool Selection: LLM selects 2-3 most relevant tools from all available MCP tools
    2. Research Execution: LLM with bound tools conducts intelligent research
    
    This approach is more efficient than calling all tools and provides better, 
    more targeted research results.
    
    The retriever requires a researcher instance to access:
    - mcp_configs: List of MCP server configurations
    - cfg: Configuration object with LLM settings and parameters
    - add_costs: Method for tracking research costs
    """

    def __init__(
        self, 
        query: str, 
        headers: Optional[Dict[str, str]] = None,
        query_domains: Optional[List[str]] = None,
        websocket=None,
        researcher=None,
        **kwargs
    ):
        """
        Initialize the MCP Retriever.
        
        Args:
            query (str): The search query string.
            headers (dict, optional): Headers containing MCP configuration.
            query_domains (list, optional): List of domains to search (not used in MCP).
            websocket: WebSocket for stream logging.
            researcher: Researcher instance containing mcp_configs and cfg.
            **kwargs: Additional arguments (for compatibility).
        """
        self.query = query
        self.headers = headers or {}
        self.query_domains = query_domains or []
        self.websocket = websocket
        self.researcher = researcher
        
        # Extract mcp_configs and config from the researcher instance
        self.mcp_configs = self._get_mcp_configs()
        self.cfg = self._get_config()
        
        # Initialize tool selection cache
        self._selected_tools_cache = None
        self._all_tools_cache = None
        
        # Initialize client management
        self._client = None
        self._client_lock = asyncio.Lock()
        
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
        if self.researcher and hasattr(self.researcher, 'mcp_configs'):
            return self.researcher.mcp_configs or []
        return []

    def _get_config(self):
        """
        Get configuration from the researcher instance.
        
        Returns:
            Config: Configuration object with LLM settings.
        """
        if self.researcher and hasattr(self.researcher, 'cfg'):
            return self.researcher.cfg
        
        # If no config available, this is a critical error
        logger.error("No config found in researcher instance. MCPRetriever requires a researcher instance with cfg attribute.")
        raise ValueError("MCPRetriever requires a researcher instance with cfg attribute containing LLM configuration")

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

    async def _call_llm_for_tool_selection(self, prompt: str) -> str:
        """
        Call the LLM using the existing create_chat_completion function for tool selection.
        
        Args:
            prompt (str): The prompt to send to the LLM.
            
        Returns:
            str: The generated text response.
        """
        if not self.cfg:
            logger.warning("No config available for LLM call")
            await self._stream_log("⚠️ No config available for LLM call")
            return ""
            
        try:
            from gpt_researcher.utils.llm import create_chat_completion
            
            # Create messages for the LLM
            messages = [{"role": "user", "content": prompt}]
            
            # Use the strategic LLM for tool selection (as it's more complex reasoning)
            result = await create_chat_completion(
                model=self.cfg.strategic_llm_model,
                messages=messages,
                temperature=0.0,  # Low temperature for consistent tool selection
                llm_provider=self.cfg.strategic_llm_provider,
                llm_kwargs=self.cfg.llm_kwargs,
                cost_callback=self.researcher.add_costs if self.researcher and hasattr(self.researcher, 'add_costs') else None,
            )
            return result
        except Exception as e:
            logger.error(f"Error calling LLM for tool selection: {e}")
            await self._stream_log(f"❌ Error calling LLM: {str(e)}")
            return ""

    async def _get_or_create_client(self) -> Optional[object]:
        """
        Get or create a MultiServerMCPClient with proper lifecycle management.
        
        Returns:
            MultiServerMCPClient: The client instance or None if creation fails
        """
        async with self._client_lock:
            if self._client is not None:
                return self._client
                
            if not HAS_MCP_ADAPTERS:
                await self._stream_log("❌ langchain-mcp-adapters not installed")
                return None
                
            if not self.mcp_configs:
                await self._stream_log("❌ No MCP server configurations found")
                return None
                
            try:
                # Convert configs to langchain format
                server_configs = self._convert_configs_to_langchain_format()
                await self._stream_log(f"🔧 Creating MCP client for {len(server_configs)} server(s)")
                
                # Initialize the MultiServerMCPClient
                self._client = MultiServerMCPClient(server_configs)
                
                return self._client
                
            except Exception as e:
                logger.error(f"Error creating MCP client: {e}")
                await self._stream_log(f"❌ Error creating MCP client: {str(e)}")
                return None

    async def _close_client(self):
        """
        Properly close the MCP client and clean up resources.
        """
        async with self._client_lock:
            if self._client is not None:
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
                    self._client = None

    async def _get_all_tools(self) -> List:
        """
        Get all available tools from MCP servers.
        
        Returns:
            List: All available MCP tools
        """
        if self._all_tools_cache is not None:
            return self._all_tools_cache
            
        client = await self._get_or_create_client()
        if not client:
            return []
            
        try:
            # Get tools from all servers
            all_tools = await client.get_tools()
            
            if all_tools:
                await self._stream_log(f"📋 Loaded {len(all_tools)} total tools from MCP servers")
                self._all_tools_cache = all_tools
                return all_tools
            else:
                await self._stream_log("⚠️ No tools available from MCP servers")
                return []
                
        except Exception as e:
            logger.error(f"Error getting MCP tools: {e}")
            await self._stream_log(f"❌ Error getting MCP tools: {str(e)}")
            return []

    async def _select_relevant_tools(self, all_tools: List, max_tools: int = 3) -> List:
        """
        Use LLM to select the most relevant tools for the research query.
        
        Args:
            all_tools: List of all available tools
            max_tools: Maximum number of tools to select (default: 3)
            
        Returns:
            List: Selected tools most relevant for the query
        """
        if not all_tools:
            return []
            
        await self._stream_log(f"🧠 Using LLM to select {max_tools} most relevant tools from {len(all_tools)} available")
        
        # Create tool descriptions for LLM analysis
        tools_info = []
        for i, tool in enumerate(all_tools):
            tool_info = {
                "index": i,
                "name": tool.name,
                "description": tool.description or "No description available"
            }
            tools_info.append(tool_info)
        
        # Create prompt for intelligent tool selection
        prompt = f"""You are a research assistant helping to select the most relevant tools for a research query.

RESEARCH QUERY: "{self.query}"

AVAILABLE TOOLS:
{json.dumps(tools_info, indent=2)}

TASK: Analyze the tools and select EXACTLY {max_tools} tools that are most relevant for researching the given query.

SELECTION CRITERIA:
- Choose tools that can provide information, data, or insights related to the query
- Prioritize tools that can search, retrieve, or access relevant content
- Consider tools that complement each other (e.g., different data sources)
- Exclude tools that are clearly unrelated to the research topic

Return a JSON object with this exact format:
{{
  "selected_tools": [
    {{
      "index": 0,
      "name": "tool_name",
      "relevance_score": 9,
      "reason": "Detailed explanation of why this tool is relevant"
    }}
  ],
  "selection_reasoning": "Overall explanation of the selection strategy"
}}

Select exactly {max_tools} tools, ranked by relevance to the research query.
"""

        try:
            # Call LLM for tool selection
            response = await self._call_llm_for_tool_selection(prompt)
            
            if not response:
                await self._stream_log("⚠️ No LLM response for tool selection, using fallback")
                return self._fallback_tool_selection(all_tools, max_tools)
            
            # Log a preview of the LLM response for debugging
            response_preview = response[:500] + "..." if len(response) > 500 else response
            await self._stream_log(f"🧠 LLM tool selection response: {response_preview}")
            
            # Parse LLM response
            try:
                selection_result = json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    try:
                        selection_result = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        await self._stream_log("⚠️ Could not parse extracted JSON, using fallback")
                        return self._fallback_tool_selection(all_tools, max_tools)
                else:
                    await self._stream_log("⚠️ No JSON found in LLM response, using fallback")
                    return self._fallback_tool_selection(all_tools, max_tools)
            
            selected_tools = []
            
            # Process selected tools
            for tool_selection in selection_result.get("selected_tools", []):
                tool_index = tool_selection.get("index")
                tool_name = tool_selection.get("name", "")
                reason = tool_selection.get("reason", "")
                relevance_score = tool_selection.get("relevance_score", 0)
                
                if tool_index is not None and 0 <= tool_index < len(all_tools):
                    selected_tools.append(all_tools[tool_index])
                    await self._stream_log(f"✅ Selected tool '{tool_name}' (score: {relevance_score}): {reason}")
            
            if len(selected_tools) == 0:
                await self._stream_log("⚠️ No tools selected by LLM, using fallback selection")
                return self._fallback_tool_selection(all_tools, max_tools)
            
            # Log the overall selection reasoning
            selection_reasoning = selection_result.get("selection_reasoning", "No reasoning provided")
            await self._stream_log(f"🎯 LLM selection strategy: {selection_reasoning}")
            
            await self._stream_log(f"🎯 LLM selected {len(selected_tools)} tools for research")
            return selected_tools
            
        except Exception as e:
            logger.error(f"Error in LLM tool selection: {e}")
            await self._stream_log(f"❌ Error in LLM tool selection: {str(e)}")
            await self._stream_log("⚠️ Falling back to pattern-based selection")
            return self._fallback_tool_selection(all_tools, max_tools)

    def _fallback_tool_selection(self, all_tools: List, max_tools: int) -> List:
        """
        Fallback tool selection using pattern matching if LLM selection fails.
        
        Args:
            all_tools: List of all available tools
            max_tools: Maximum number of tools to select
            
        Returns:
            List: Selected tools
        """
        # Define patterns for research-relevant tools
        research_patterns = [
            'search', 'get', 'read', 'fetch', 'find', 'list', 'query', 
            'lookup', 'retrieve', 'browse', 'view', 'show', 'describe'
        ]
        
        scored_tools = []
        
        for tool in all_tools:
            tool_name = tool.name.lower()
            tool_description = (tool.description or "").lower()
            
            # Calculate relevance score based on pattern matching
            score = 0
            for pattern in research_patterns:
                if pattern in tool_name:
                    score += 3
                if pattern in tool_description:
                    score += 1
            
            if score > 0:
                scored_tools.append((tool, score))
        
        # Sort by score and take top tools
        scored_tools.sort(key=lambda x: x[1], reverse=True)
        selected_tools = [tool for tool, score in scored_tools[:max_tools]]
        
        for i, (tool, score) in enumerate(scored_tools[:max_tools]):
            logger.info(f"🔍 Fallback selected tool {i+1}: {tool.name} (score: {score})")
        
        return selected_tools

    async def _conduct_research_with_tools(self, selected_tools: List) -> List[Dict[str, str]]:
        """
        Use LLM with bound tools to conduct intelligent research.
        
        Args:
            selected_tools: List of selected MCP tools
            
        Returns:
            List[Dict[str, str]]: Research results in standard format
        """
        if not selected_tools:
            await self._stream_log("⚠️ No tools available for research")
            return []
            
        await self._stream_log(f"🔬 Conducting research using {len(selected_tools)} selected tools")
        
        try:
            from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
            
            # Create LLM provider using the config
            provider_kwargs = {
                'model': self.cfg.strategic_llm_model,
                **self.cfg.llm_kwargs
            }
            
            llm_provider = GenericLLMProvider.from_provider(
                self.cfg.strategic_llm_provider, 
                **provider_kwargs
            )
            
            # Bind tools to LLM
            llm_with_tools = llm_provider.llm.bind_tools(selected_tools)
            
            # Create research prompt
            research_prompt = f"""You are a research assistant with access to specialized tools. Your task is to research the following query and provide comprehensive, accurate information.

RESEARCH QUERY: "{self.query}"

INSTRUCTIONS:
1. Use the available tools to gather relevant information about the query
2. Call multiple tools if needed to get comprehensive coverage
3. If a tool call fails or returns empty results, try alternative approaches
4. Synthesize information from multiple sources when possible
5. Focus on factual, relevant information that directly addresses the query

AVAILABLE TOOLS: {[tool.name for tool in selected_tools]}

Please conduct thorough research and provide your findings. Use the tools strategically to gather the most relevant and comprehensive information."""

            # Create messages
            messages = [{"role": "user", "content": research_prompt}]
            
            # Invoke LLM with tools
            await self._stream_log("🧠 LLM researching with bound tools...")
            response = await llm_with_tools.ainvoke(messages)
            
            # Process tool calls and results
            research_results = []
            
            # Check if the LLM made tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                await self._stream_log(f"🔧 LLM made {len(response.tool_calls)} tool calls")
                
                # Process each tool call
                for i, tool_call in enumerate(response.tool_calls, 1):
                    tool_name = tool_call.get("name", "unknown")
                    tool_args = tool_call.get("args", {})
                    
                    await self._stream_log(f"🔍 Executing tool {i}/{len(response.tool_calls)}: {tool_name}")
                    
                    # Log the tool arguments for transparency
                    if tool_args:
                        args_str = ", ".join([f"{k}={v}" for k, v in tool_args.items()])
                        await self._stream_log(f"📋 Tool arguments: {args_str}")
                    
                    try:
                        # Find the tool by name
                        tool = next((t for t in selected_tools if t.name == tool_name), None)
                        if not tool:
                            await self._stream_log(f"⚠️ Tool {tool_name} not found in selected tools")
                            continue
                        
                        # Execute the tool
                        if hasattr(tool, 'ainvoke'):
                            result = await tool.ainvoke(tool_args)
                        elif hasattr(tool, 'invoke'):
                            result = tool.invoke(tool_args)
                        else:
                            result = await tool(tool_args) if asyncio.iscoroutinefunction(tool) else tool(tool_args)
                        
                        # Log the actual tool response for debugging
                        if result:
                            result_preview = str(result)[:500] + "..." if len(str(result)) > 500 else str(result)
                            await self._stream_log(f"📄 Tool {tool_name} response preview: {result_preview}")
                            
                            # Process the result
                            formatted_results = self._process_tool_result(tool_name, result)
                            research_results.extend(formatted_results)
                            await self._stream_log(f"✅ Tool {tool_name} returned {len(formatted_results)} formatted results")
                            
                            # Log details of each formatted result
                            for j, formatted_result in enumerate(formatted_results):
                                title = formatted_result.get("title", "No title")
                                content_preview = formatted_result.get("body", "")[:200] + "..." if len(formatted_result.get("body", "")) > 200 else formatted_result.get("body", "")
                                await self._stream_log(f"📋 Result {j+1}: '{title}' - Content: {content_preview}")
                        else:
                            await self._stream_log(f"⚠️ Tool {tool_name} returned empty result")
                            
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}")
                        await self._stream_log(f"❌ Error executing tool {tool_name}: {str(e)}")
                        continue
                        
            # Also include the LLM's own analysis/response as a result
            if hasattr(response, 'content') and response.content:
                llm_analysis = {
                    "title": f"LLM Analysis: {self.query}",
                    "href": "mcp://llm_analysis",
                    "body": response.content
                }
                research_results.append(llm_analysis)
                
                # Log LLM analysis content
                analysis_preview = response.content[:300] + "..." if len(response.content) > 300 else response.content
                await self._stream_log(f"🧠 LLM Analysis: {analysis_preview}")
                await self._stream_log("📝 Added LLM analysis to results")
            
            await self._stream_log(f"🎯 Research completed with {len(research_results)} total results")
            return research_results
            
        except Exception as e:
            logger.error(f"Error in LLM research with tools: {e}")
            await self._stream_log(f"❌ Error in LLM research: {str(e)}")
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

    async def search_async(self, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Perform an async search using MCP tools with intelligent two-stage approach.
        
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
            await self._stream_log("❌ MCP retriever cannot proceed without server configurations.")
            return []  # Return empty instead of raising to allow research to continue
            
        # Log to help debug the integration flow
        logger.info(f"MCPRetriever.search_async called for query: {self.query}")
            
        try:
            # Stage 1: Get all available tools
            await self._stream_log("🔧 Stage 1: Getting all available MCP tools")
            all_tools = await self._get_all_tools()
            
            if not all_tools:
                await self._stream_log("⚠️ No MCP tools available, skipping MCP research")
                return []
            
            # Stage 2: Select most relevant tools
            selected_tools = await self._select_relevant_tools(all_tools, max_tools=3)
            
            if not selected_tools:
                await self._stream_log("⚠️ No relevant tools selected, skipping MCP research")
                return []
            
            # Stage 3: Conduct research with selected tools
            await self._stream_log("🔬 Stage 3: Conducting research with selected tools")
            results = await self._conduct_research_with_tools(selected_tools)
            
            # Limit the number of results
            if len(results) > max_results:
                logger.info(f"Limiting {len(results)} MCP results to {max_results}")
                results = results[:max_results]
            
            # Log result summary with actual content samples
            logger.info(f"MCPRetriever returning {len(results)} results")
            await self._stream_log(f"✅ MCP research completed: {len(results)} results obtained")
            
            # Log detailed content samples for debugging
            if results:
                total_content_length = sum(len(result.get("body", "")) for result in results)
                await self._stream_log(f"📊 Total content gathered: {total_content_length:,} characters")
                
                # Show samples of the first few results
                for i, result in enumerate(results[:3]):  # Show first 3 results
                    title = result.get("title", "No title")
                    url = result.get("href", "No URL")
                    content = result.get("body", "")
                    content_length = len(content)
                    content_sample = content[:400] + "..." if len(content) > 400 else content
                    
                    await self._stream_log(f"📄 Result {i+1}/{len(results)}: '{title}'")
                    await self._stream_log(f"🔗 URL: {url}")
                    await self._stream_log(f"📝 Content ({content_length:,} chars): {content_sample}")
                    
                if len(results) > 3:
                    remaining_results = len(results) - 3
                    remaining_content = sum(len(result.get("body", "")) for result in results[3:])
                    await self._stream_log(f"📚 ... and {remaining_results} more results ({remaining_content:,} chars)")
                    
            return results
            
        except Exception as e:
            logger.error(f"Error in MCP search: {e}")
            await self._stream_log(f"❌ Error in MCP search: {str(e)}")
            return []
        finally:
            # Ensure client cleanup after search completes
            try:
                await self._close_client()
            except Exception as e:
                logger.error(f"Error during client cleanup: {e}")

    def search(self, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Perform a search using MCP tools with intelligent two-stage approach.
        
        This is the synchronous interface required by GPT Researcher.
        It wraps the async search_async method.
        
        Args:
            max_results: Maximum number of results to return.
            
        Returns:
            List[Dict[str, str]]: The search results.
        """
        # Check if we have any server configurations
        if not self.mcp_configs:
            error_msg = "No MCP server configurations available. Please provide mcp_configs parameter to GPTResearcher."
            logger.error(error_msg)
            self._stream_log_sync("❌ MCP retriever cannot proceed without server configurations.")
            return []  # Return empty instead of raising to allow research to continue
            
        # Log to help debug the integration flow
        logger.info(f"MCPRetriever.search called for query: {self.query}")
        
        try:
            # Handle the async/sync boundary properly
            try:
                # Try to get the current event loop
                loop = asyncio.get_running_loop()
                # If we're in an async context, we need to schedule the coroutine
                # This is a bit tricky - we'll create a task and let it run
                import concurrent.futures
                import threading
                
                # Create a new event loop in a separate thread
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(self.search_async(max_results))
                        return result
                    finally:
                        # Enhanced cleanup procedure for MCP connections
                        try:
                            # Cancel all pending tasks with a timeout
                            pending = asyncio.all_tasks(new_loop)
                            for task in pending:
                                task.cancel()
                            
                            # Wait for cancelled tasks to complete with timeout
                            if pending:
                                try:
                                    new_loop.run_until_complete(
                                        asyncio.wait_for(
                                            asyncio.gather(*pending, return_exceptions=True),
                                            timeout=5.0  # 5 second timeout for cleanup
                                        )
                                    )
                                except asyncio.TimeoutError:
                                    logger.debug("Timeout during task cleanup, continuing...")
                                except Exception:
                                    pass  # Ignore other cleanup errors
                        except Exception:
                            pass  # Ignore cleanup errors
                        finally:
                            try:
                                # Give the loop a moment to finish any final cleanup
                                import time
                                time.sleep(0.1)
                                
                                # Force garbage collection to clean up any remaining references
                                import gc
                                gc.collect()
                                
                                # Additional time for HTTP clients to finish their cleanup
                                time.sleep(0.2)
                                
                                # Close the loop
                                if not new_loop.is_closed():
                                    new_loop.close()
                            except Exception:
                                pass  # Ignore close errors
                
                # Run in a thread pool to avoid blocking the main event loop
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    results = future.result(timeout=300)  # 5 minute timeout
                    
            except RuntimeError:
                # No event loop is running, we can run directly
                results = asyncio.run(self.search_async(max_results))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in MCP search: {e}")
            self._stream_log_sync(f"❌ Error in MCP search: {str(e)}")
            # Return empty results instead of raising to allow research to continue
            return [] 