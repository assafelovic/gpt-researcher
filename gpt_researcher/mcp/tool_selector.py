"""
MCP Tool Selection Module

Handles intelligent tool selection using LLM analysis.
"""
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MCPToolSelector:
    """
    Handles intelligent selection of MCP tools using LLM analysis.
    
    Responsible for:
    - Analyzing available tools with LLM
    - Selecting the most relevant tools for a query
    - Providing fallback selection mechanisms
    """

    def __init__(self, cfg, researcher=None):
        """
        Initialize the tool selector.
        
        Args:
            cfg: Configuration object with LLM settings
            researcher: Researcher instance for cost tracking
        """
        self.cfg = cfg
        self.researcher = researcher

    async def select_relevant_tools(self, query: str, all_tools: List, max_tools: int = 3) -> List:
        """
        Use LLM to select the most relevant tools for the research query.
        
        Args:
            query: Research query
            all_tools: List of all available tools
            max_tools: Maximum number of tools to select (default: 3)
            
        Returns:
            List: Selected tools most relevant for the query
        """
        if not all_tools:
            return []

        if len(all_tools) < max_tools:
            max_tools = len(all_tools)
            
        logger.info(f"Using LLM to select {max_tools} most relevant tools from {len(all_tools)} available")
        
        # Create tool descriptions for LLM analysis
        tools_info = []
        for i, tool in enumerate(all_tools):
            tool_info = {
                "index": i,
                "name": tool.name,
                "description": tool.description or "No description available"
            }
            tools_info.append(tool_info)
        
        # Import here to avoid circular imports
        from ..prompts import PromptFamily
        
        # Create prompt for intelligent tool selection
        prompt = PromptFamily.generate_mcp_tool_selection_prompt(query, tools_info, max_tools)

        try:
            # Call LLM for tool selection
            response = await self._call_llm_for_tool_selection(prompt)
            
            if not response:
                logger.warning("No LLM response for tool selection, using fallback")
                return self._fallback_tool_selection(all_tools, max_tools)
            
            # Log a preview of the LLM response for debugging
            response_preview = response[:500] + "..." if len(response) > 500 else response
            logger.debug(f"LLM tool selection response: {response_preview}")
            
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
                        logger.warning("Could not parse extracted JSON, using fallback")
                        return self._fallback_tool_selection(all_tools, max_tools)
                else:
                    logger.warning("No JSON found in LLM response, using fallback")
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
                    logger.info(f"Selected tool '{tool_name}' (score: {relevance_score}): {reason}")
            
            if len(selected_tools) == 0:
                logger.warning("No tools selected by LLM, using fallback selection")
                return self._fallback_tool_selection(all_tools, max_tools)
            
            # Log the overall selection reasoning
            selection_reasoning = selection_result.get("selection_reasoning", "No reasoning provided")
            logger.info(f"LLM selection strategy: {selection_reasoning}")
            
            logger.info(f"LLM selected {len(selected_tools)} tools for research")
            return selected_tools
            
        except Exception as e:
            logger.error(f"Error in LLM tool selection: {e}")
            logger.warning("Falling back to pattern-based selection")
            return self._fallback_tool_selection(all_tools, max_tools)

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
            return ""
            
        try:
            from ..utils.llm import create_chat_completion
            
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
            return ""

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
            logger.info(f"Fallback selected tool {i+1}: {tool.name} (score: {score})")
        
        return selected_tools 