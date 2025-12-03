"""
Tool-enabled LLM utilities for GPT Researcher

This module provides provider-agnostic tool calling functionality using LangChain's
unified interface. It allows any LLM provider that supports function calling to use
tools seamlessly.
"""

import asyncio
import logging
from typing import Any, Dict, List, Tuple, Callable, Optional
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool

from .llm import create_chat_completion

logger = logging.getLogger(__name__)


async def create_chat_completion_with_tools(
    messages: List[Dict[str, str]],
    tools: List[Callable],
    model: str | None = None,
    temperature: float | None = 0.4,
    max_tokens: int | None = 4000,
    llm_provider: str | None = None,
    llm_kwargs: Dict[str, Any] | None = None,
    cost_callback: Callable = None,
    websocket: Any | None = None,
    **kwargs
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Create a chat completion with tool calling support across all LLM providers.
    
    This function uses LangChain's bind_tools() to enable function calling in a 
    provider-agnostic way. The AI decides autonomously when and how to use tools.
    
    Args:
        messages: List of chat messages with role and content
        tools: List of LangChain tool functions (decorated with @tool)
        model: The model to use (from config)
        temperature: Temperature for generation
        max_tokens: Maximum tokens to generate
        llm_provider: LLM provider name (from config)
        llm_kwargs: Additional LLM keyword arguments
        cost_callback: Callback function for cost tracking
        websocket: Optional websocket for streaming
        **kwargs: Additional arguments
        
    Returns:
        Tuple of (response_content, tool_calls_metadata)
        
    Raises:
        Exception: If tool-enabled completion fails, falls back to simple completion
    """
    try:
        from ..llm_provider.generic.base import GenericLLMProvider
        
        # Create LLM provider using the config
        provider_kwargs = {
            'model': model,
            **(llm_kwargs or {})
        }
        
        llm_provider_instance = GenericLLMProvider.from_provider(
            llm_provider, 
            **provider_kwargs
        )
        
        # Convert messages to LangChain format
        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        
        # Bind tools to the LLM - this works across all LangChain providers that support function calling
        llm_with_tools = llm_provider_instance.llm.bind_tools(tools)
        
        # Invoke the LLM with tools - this will handle the full conversation flow
        logger.info(f"Invoking LLM with {len(tools)} available tools")
        
        # For tool calling, we need to handle the full conversation including tool responses
        from langchain_core.messages import ToolMessage
        
        # First call to LLM
        response = await llm_with_tools.ainvoke(lc_messages)
        
        # Process tool calls if any were made
        tool_calls_metadata = []
        if hasattr(response, 'tool_calls') and response.tool_calls:
            logger.info(f"LLM made {len(response.tool_calls)} tool calls")
            
            # Add the assistant's response with tool calls to the conversation
            lc_messages.append(response)
            
            # Execute each tool call and add results to conversation
            for tool_call in response.tool_calls:
                tool_name = tool_call.get('name', 'unknown')
                tool_args = tool_call.get('args', {})
                tool_id = tool_call.get('id', '')
                
                logger.info(f"Tool called: {tool_name}")
                if tool_args:
                    args_str = ", ".join([f"{k}={v}" for k, v in tool_args.items()])
                    logger.debug(f"Tool arguments: {args_str}")
                
                # Find and execute the tool
                tool_result = "Tool execution failed"
                for tool in tools:
                    if tool.name == tool_name:
                        try:
                            if hasattr(tool, 'ainvoke'):
                                tool_result = await tool.ainvoke(tool_args)
                            elif hasattr(tool, 'invoke'):
                                tool_result = tool.invoke(tool_args)
                            else:
                                tool_result = await tool(**tool_args) if asyncio.iscoroutinefunction(tool) else tool(**tool_args)
                            break
                        except Exception as e:
                            logger.error(f"Error executing tool {tool_name}: {e}")
                            tool_result = f"Tool error: {str(e)}"
                
                # Add tool result to conversation
                tool_message = ToolMessage(content=str(tool_result), tool_call_id=tool_id)
                lc_messages.append(tool_message)
                
                # Add to metadata
                tool_calls_metadata.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "call_id": tool_id,
                    "result": str(tool_result)[:200] + "..." if len(str(tool_result)) > 200 else str(tool_result)
                })
            
            # Get final response from LLM after tool execution
            logger.info("Getting final response from LLM after tool execution")
            final_response = await llm_with_tools.ainvoke(lc_messages)
            
            # Track costs if callback provided
            if cost_callback:
                from .costs import estimate_llm_cost
                # Calculate costs for both calls
                llm_costs = estimate_llm_cost(str(lc_messages), final_response.content or "")
                cost_callback(llm_costs)
            
            return final_response.content, tool_calls_metadata
        
        else:
            # No tool calls, return regular response
            if cost_callback:
                from .costs import estimate_llm_cost
                llm_costs = estimate_llm_cost(str(messages), response.content or "")
                cost_callback(llm_costs)
            
            return response.content, []
        
    except Exception as e:
        logger.error(f"Error in tool-enabled chat completion: {str(e)}")
        logger.info("Falling back to simple chat completion without tools")
        
        # Fallback to simple chat completion without tools
        response = await create_chat_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            llm_provider=llm_provider,
            llm_kwargs=llm_kwargs,
            cost_callback=cost_callback,
            websocket=websocket,
            **kwargs
        )
        return response, []


def create_search_tool(search_function: Callable[[str], Dict]) -> Callable:
    """
    Create a standardized search tool for use with tool-enabled chat completions.
    
    Args:
        search_function: Function that takes a query string and returns search results
        
    Returns:
        LangChain tool function decorated with @tool
    """
    @tool
    def search_tool(query: str) -> str:
        """Search for current events or online information when you need new knowledge that doesn't exist in the current context"""
        try:
            results = search_function(query)
            if results and 'results' in results:
                search_content = f"Search results for '{query}':\n\n"
                for result in results['results'][:5]:
                    search_content += f"Title: {result.get('title', '')}\n"
                    search_content += f"Content: {result.get('content', '')[:300]}...\n"
                    search_content += f"URL: {result.get('url', '')}\n\n"
                return search_content
            else:
                return f"No search results found for: {query}"
        except Exception as e:
            logger.error(f"Search tool error: {str(e)}")
            return f"Search error: {str(e)}"
    
    return search_tool


def create_custom_tool(
    name: str,
    description: str, 
    function: Callable,
    parameter_schema: Optional[Dict] = None
) -> Callable:
    """
    Create a custom tool for use with tool-enabled chat completions.
    
    Args:
        name: Name of the tool
        description: Description of what the tool does
        function: The actual function to execute
        parameter_schema: Optional schema for function parameters
        
    Returns:
        LangChain tool function decorated with @tool
    """
    @tool
    def custom_tool(*args, **kwargs) -> str:
        try:
            result = function(*args, **kwargs)
            return str(result) if result is not None else "Tool executed successfully"
        except Exception as e:
            logger.error(f"Custom tool '{name}' error: {str(e)}")
            return f"Tool error: {str(e)}"
    
    # Set tool metadata
    custom_tool.name = name
    custom_tool.description = description
    
    return custom_tool


# Utility function for common tool patterns
def get_available_providers_with_tools() -> List[str]:
    """
    Get list of LLM providers that support tool calling.
    
    Returns:
        List of provider names that support function calling
    """
    # These are the providers known to support function calling in LangChain
    return [
        "openai",
        "anthropic", 
        "google_genai",
        "azure_openai",
        "fireworks",
        "groq",
        # Note: This list may expand as more providers add function calling support
    ]


def supports_tools(provider: str) -> bool:
    """
    Check if a given provider supports tool calling.
    
    Args:
        provider: LLM provider name
        
    Returns:
        True if provider supports tools, False otherwise
    """
    return provider in get_available_providers_with_tools()
