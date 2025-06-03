"""
MCP Research Execution Skill

Handles research execution using selected MCP tools as a skill component.
"""
import asyncio
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class MCPResearchSkill:
    """
    Handles research execution using selected MCP tools.
    
    Responsible for:
    - Executing research with LLM and bound tools
    - Processing tool results into standard format
    - Managing tool execution and error handling
    """

    def __init__(self, cfg, researcher=None):
        """
        Initialize the MCP research skill.
        
        Args:
            cfg: Configuration object with LLM settings
            researcher: Researcher instance for cost tracking
        """
        self.cfg = cfg
        self.researcher = researcher

    async def conduct_research_with_tools(self, query: str, selected_tools: List) -> List[Dict[str, str]]:
        """
        Use LLM with bound tools to conduct intelligent research.
        
        Args:
            query: Research query
            selected_tools: List of selected MCP tools
            
        Returns:
            List[Dict[str, str]]: Research results in standard format
        """
        if not selected_tools:
            logger.warning("No tools available for research")
            return []
            
        logger.info(f"Conducting research using {len(selected_tools)} selected tools")
        
        try:
            from ..llm_provider.generic.base import GenericLLMProvider
            
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
            
            # Import here to avoid circular imports
            from ..prompts import PromptFamily
            
            # Create research prompt
            research_prompt = PromptFamily.generate_mcp_research_prompt(query, selected_tools)

            # Create messages
            messages = [{"role": "user", "content": research_prompt}]
            
            # Invoke LLM with tools
            logger.info("LLM researching with bound tools...")
            response = await llm_with_tools.ainvoke(messages)
            
            # Process tool calls and results
            research_results = []
            
            # Check if the LLM made tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info(f"LLM made {len(response.tool_calls)} tool calls")
                
                # Process each tool call
                for i, tool_call in enumerate(response.tool_calls, 1):
                    tool_name = tool_call.get("name", "unknown")
                    tool_args = tool_call.get("args", {})
                    
                    logger.info(f"Executing tool {i}/{len(response.tool_calls)}: {tool_name}")
                    
                    # Log the tool arguments for transparency
                    if tool_args:
                        args_str = ", ".join([f"{k}={v}" for k, v in tool_args.items()])
                        logger.debug(f"Tool arguments: {args_str}")
                    
                    try:
                        # Find the tool by name
                        tool = next((t for t in selected_tools if t.name == tool_name), None)
                        if not tool:
                            logger.warning(f"Tool {tool_name} not found in selected tools")
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
                            logger.debug(f"Tool {tool_name} response preview: {result_preview}")
                            
                            # Process the result
                            formatted_results = self._process_tool_result(tool_name, result)
                            research_results.extend(formatted_results)
                            logger.info(f"Tool {tool_name} returned {len(formatted_results)} formatted results")
                            
                            # Log details of each formatted result
                            for j, formatted_result in enumerate(formatted_results):
                                title = formatted_result.get("title", "No title")
                                content_preview = formatted_result.get("body", "")[:200] + "..." if len(formatted_result.get("body", "")) > 200 else formatted_result.get("body", "")
                                logger.debug(f"Result {j+1}: '{title}' - Content: {content_preview}")
                        else:
                            logger.warning(f"Tool {tool_name} returned empty result")
                            
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}")
                        continue
                        
            # Also include the LLM's own analysis/response as a result
            if hasattr(response, 'content') and response.content:
                llm_analysis = {
                    "title": f"LLM Analysis: {query}",
                    "href": "mcp://llm_analysis",
                    "body": response.content
                }
                research_results.append(llm_analysis)
                
                # Log LLM analysis content
                analysis_preview = response.content[:300] + "..." if len(response.content) > 300 else response.content
                logger.debug(f"LLM Analysis: {analysis_preview}")
                logger.info("Added LLM analysis to results")
            
            logger.info(f"Research completed with {len(research_results)} total results")
            return research_results
            
        except Exception as e:
            logger.error(f"Error in LLM research with tools: {e}")
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