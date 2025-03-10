"""
Finalizer Agent for Deep Research

This agent is responsible for finalizing the research process and preparing the final context.
"""

from typing import Dict, Any, List
import asyncio

from ...agents.utils.views import print_agent_output
from .base import DeepResearchAgent, trim_context_to_word_limit

class FinalizerAgent(DeepResearchAgent):
    """
    Agent responsible for finalizing the research process and preparing the final context.
    """
    
    def __init__(self, websocket=None, stream_output=None, tone=None, headers=None):
        """
        Initialize the agent.
        
        Args:
            websocket: Optional websocket for streaming output
            stream_output: Optional stream output function
            tone: Optional tone for the research
            headers: Optional headers for API requests
        """
        super().__init__(websocket, stream_output, tone, headers)
    
    async def finalize_research(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finalize the research process and prepare the final context.
        
        Args:
            research_state: Current research state
            
        Returns:
            Updated research state with final context
        """
        # Log the action
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "finalizing_research",
                "Finalizing research and preparing final context...",
                self.websocket,
            )
        else:
            print_agent_output(
                "Finalizing research and preparing final context...",
                agent="FINALIZER",
            )
        
        # Get the context items
        context_items = research_state.get("context_items", [])
        
        # Get the sources
        sources = research_state.get("sources", [])
        
        # Get the citations
        citations = research_state.get("citations", {})
        
        # Get the query
        query = research_state.get("query", "")
        
        # Log the current state
        print_agent_output(
            f"Finalizing research with {len(context_items)} context items and {len(sources)} sources.",
            agent="FINALIZER",
        )
        
        # If context_items is empty but we have sources, create context from sources
        new_context_items = list(context_items)  # Create a copy to avoid modifying the original
        
        if not new_context_items and sources:
            print_agent_output(
                f"Creating context items from {len(sources)} sources.",
                agent="FINALIZER",
            )
            for source in sources:
                if isinstance(source, dict) and "content" in source:
                    title = source.get("title", "Unknown Title")
                    url = source.get("url", "")
                    content = source.get("content", "")
                    if content:
                        new_context_items.append(f"From {title} [{url}]:\n{content}")
        
        # If still no context items, create a default context
        if not new_context_items:
            print_agent_output(
                "Creating default context item since no context items or sources were found.",
                agent="FINALIZER",
            )
            new_context_items = [f"Research on: {query}\n\nNo specific research data was collected."]
        
        # Combine all context items into a single context
        combined_context = "\n\n".join(new_context_items)
        
        # Trim the context to a reasonable size if needed
        max_words = 100000  # Increased from 10000 to 100000
        
        # Import the fixed trim_context_to_word_limit function
        from .base import trim_context_to_word_limit
        
        try:
            # Use the fixed function which now returns a string
            trimmed_context = trim_context_to_word_limit(combined_context, max_words)
        except Exception as e:
            print_agent_output(
                f"Error trimming context: {str(e)}. Using original context.",
                agent="FINALIZER",
            )
            # Fallback to using the combined context directly
            trimmed_context = combined_context
        
        # Generate a summary of the research if the context is large
        summary = ""
        if len(combined_context.split()) > max_words:
            # Get model from config
            from gpt_researcher.config.config import Config
            cfg = Config()
            model = cfg.smart_llm_model
            
            # Create the prompt for generating the summary
            from ...agents.utils.llms import call_model
            prompt = [
                {
                    "role": "system",
                    "content": "You are a research summarizer. Your task is to create a concise summary of research findings."
                },
                {
                    "role": "user",
                    "content": f"""I have conducted research on the following topic:
                    
Topic: {query}

Here are the key findings:
{trimmed_context[:5000]}...

Please create a concise summary (around 500 words) of these research findings.
Focus on the most important insights, patterns, and conclusions.
"""
                }
            ]
            
            # Call the model to generate the summary
            summary = await call_model(
                prompt,
                model,
            )
            
            # Handle potential errors
            if not summary or not isinstance(summary, str):
                summary = f"Research summary for '{query}'."
        
        # Return updated research state following LangGraph pattern
        return {
            "context_items": new_context_items,  # Return updated context items
            "summary": summary,
            "final_context": trimmed_context,  # Set the final context
            "sources": sources,  # Explicitly include sources
            "citations": citations  # Explicitly include citations
        }
    
    async def run(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the finalizer agent.
        
        Args:
            research_state: Current research state
            
        Returns:
            Updated research state with final context
        """
        # Call finalize_research to generate the final context
        return await self.finalize_research(research_state) 