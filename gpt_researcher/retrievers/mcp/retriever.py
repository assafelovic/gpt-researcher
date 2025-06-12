"""
MCP-Based Research Retriever

A retriever that uses Model Context Protocol (MCP) tools for intelligent research.
This retriever implements a two-stage approach:
1. Tool Selection: LLM selects 2-3 most relevant tools from all available MCP tools
2. Research Execution: LLM uses the selected tools to conduct intelligent research
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    HAS_MCP_ADAPTERS = True
except ImportError:
    HAS_MCP_ADAPTERS = False

from ...mcp.client import MCPClientManager
from ...mcp.tool_selector import MCPToolSelector
from ...mcp.research import MCPResearchSkill
from ...mcp.streaming import MCPStreamer

logger = logging.getLogger(__name__)


class MCPRetriever:
    """
    Model Context Protocol (MCP) Retriever for GPT Researcher.
    
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
        
        # Initialize modular components
        self.client_manager = MCPClientManager(self.mcp_configs)
        self.tool_selector = MCPToolSelector(self.cfg, self.researcher)
        self.mcp_researcher = MCPResearchSkill(self.cfg, self.researcher)
        self.streamer = MCPStreamer(self.websocket)
        
        # Initialize caching
        self._all_tools_cache = None
        
        # Log initialization
        if self.mcp_configs:
            self.streamer.stream_log_sync(f"🔧 Initializing MCP retriever for query: {self.query}")
            self.streamer.stream_log_sync(f"🔧 Found {len(self.mcp_configs)} MCP server configurations")
        else:
            logger.error("No MCP server configurations found. The retriever will fail during search.")
            self.streamer.stream_log_sync("❌ CRITICAL: No MCP server configurations found. Please check documentation.")

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

    async def search_async(self, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Perform an async search using MCP tools with intelligent two-stage approach.
        
        Args:
            max_results: Maximum number of results to return.
            
        Returns:
            List[Dict[str, str]]: The search results.
        """
        # Check if we have any server configurations
        if not self.mcp_configs:
            error_msg = "No MCP server configurations available. Please provide mcp_configs parameter to GPTResearcher."
            logger.error(error_msg)
            await self.streamer.stream_error("MCP retriever cannot proceed without server configurations.")
            return []  # Return empty instead of raising to allow research to continue
            
        # Log to help debug the integration flow
        logger.info(f"MCPRetriever.search_async called for query: {self.query}")
            
        try:
            # Stage 1: Get all available tools
            await self.streamer.stream_stage_start("Stage 1", "Getting all available MCP tools")
            all_tools = await self._get_all_tools()
            
            if not all_tools:
                await self.streamer.stream_warning("No MCP tools available, skipping MCP research")
                return []
            
            # Stage 2: Select most relevant tools
            await self.streamer.stream_stage_start("Stage 2", "Selecting most relevant tools")
            selected_tools = await self.tool_selector.select_relevant_tools(self.query, all_tools, max_tools=3)
            
            if not selected_tools:
                await self.streamer.stream_warning("No relevant tools selected, skipping MCP research")
                return []
            
            # Stage 3: Conduct research with selected tools
            await self.streamer.stream_stage_start("Stage 3", "Conducting research with selected tools")
            results = await self.mcp_researcher.conduct_research_with_tools(self.query, selected_tools)
            
            # Limit the number of results
            if len(results) > max_results:
                logger.info(f"Limiting {len(results)} MCP results to {max_results}")
                results = results[:max_results]
            
            # Log result summary with actual content samples
            logger.info(f"MCPRetriever returning {len(results)} results")
            
            # Calculate total content length for summary
            total_content_length = sum(len(result.get("body", "")) for result in results)
            await self.streamer.stream_research_results(len(results), total_content_length)
            
            # Log detailed content samples for debugging
            if results:
                # Show samples of the first few results
                for i, result in enumerate(results[:3]):  # Show first 3 results
                    title = result.get("title", "No title")
                    url = result.get("href", "No URL")
                    content = result.get("body", "")
                    content_length = len(content)
                    content_sample = content[:400] + "..." if len(content) > 400 else content
                    
                    logger.debug(f"Result {i+1}/{len(results)}: '{title}'")
                    logger.debug(f"URL: {url}")
                    logger.debug(f"Content ({content_length:,} chars): {content_sample}")
                    
                if len(results) > 3:
                    remaining_results = len(results) - 3
                    remaining_content = sum(len(result.get("body", "")) for result in results[3:])
                    logger.debug(f"... and {remaining_results} more results ({remaining_content:,} chars)")
                    
            return results
            
        except Exception as e:
            logger.error(f"Error in MCP search: {e}")
            await self.streamer.stream_error(f"Error in MCP search: {str(e)}")
            return []
        finally:
            # Ensure client cleanup after search completes
            try:
                await self.client_manager.close_client()
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
            self.streamer.stream_log_sync("❌ MCP retriever cannot proceed without server configurations.")
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
            self.streamer.stream_log_sync(f"❌ Error in MCP search: {str(e)}")
            # Return empty results instead of raising to allow research to continue
            return []

    async def _get_all_tools(self) -> List:
        """
        Get all available tools from MCP servers.
        
        Returns:
            List: All available MCP tools
        """
        if self._all_tools_cache is not None:
            return self._all_tools_cache
            
        try:
            all_tools = await self.client_manager.get_all_tools()
            
            if all_tools:
                await self.streamer.stream_log(f"📋 Loaded {len(all_tools)} total tools from MCP servers")
                self._all_tools_cache = all_tools
                return all_tools
            else:
                await self.streamer.stream_warning("No tools available from MCP servers")
                return []
                
        except Exception as e:
            logger.error(f"Error getting MCP tools: {e}")
            await self.streamer.stream_error(f"Error getting MCP tools: {str(e)}")
            return [] 