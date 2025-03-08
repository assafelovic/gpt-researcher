"""
Section Writer Agent for Deep Research

This agent is responsible for generating sections from deep research data.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List

from ...agents.utils.llms import call_model
from ...agents.utils.views import print_agent_output
from .base import DeepResearchAgent

class SectionWriterAgent(DeepResearchAgent):
    """
    Agent responsible for generating sections from deep research data.
    """
    
    def __init__(self, websocket=None, stream_output=None, headers=None):
        """
        Initialize the agent.
        
        Args:
            websocket: Optional websocket for streaming output
            stream_output: Optional stream output function
            headers: Optional headers for API requests
        """
        super().__init__(websocket, stream_output, headers)
        
    async def generate_sections(self, research_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate sections from deep research data.
        
        Args:
            research_state: Research state containing deep research data
            
        Returns:
            List of section objects with title and content
        """
        query = research_state.get("query", "")
        context = research_state.get("context", "")
        task = research_state.get("task", {})
        sources = research_state.get("sources", [])
        citations = research_state.get("citations", {})
        
        # The context already contains the research results with sources
        # We don't need to check for empty sources as the context itself is the source
        # Just ensure the context is not empty
        if not context:
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "error",
                    "No research context found. Cannot generate sections without research data.",
                    self.websocket,
                )
            else:
                print_agent_output(
                    "No research context found. Cannot generate sections without research data.",
                    agent="SECTION_WRITER",
                )
            raise ValueError("No research context found. Cannot generate sections without research data.")
        
        # Get model from task or use a default model if None
        model = task.get("model")
        if model is None:
            from gpt_researcher.config.config import Config
            cfg = Config()
            model = cfg.smart_llm_model  # Use the default smart model from config
            
        # Log the action
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "generating_sections",
                f"Generating sections from deep research data with {len(sources)} sources...",
                self.websocket,
            )
        else:
            print_agent_output(
                f"Generating sections from deep research data with {len(sources)} sources...",
                agent="SECTION_WRITER",
            )
        
        # Format sources for better context
        formatted_sources = []
        for source in sources:
            if isinstance(source, dict) and "url" in source:
                title = source.get("title", "Unknown Title")
                url = source.get("url", "")
                content = source.get("content", "")
                formatted_sources.append(f"Source: {title}\nURL: {url}\nContent: {content}")
            elif isinstance(source, str):
                formatted_sources.append(source)
                
        # Create the prompt for generating sections
        prompt = [
            {
                "role": "system",
                "content": "You are a research writer. Your sole purpose is to organize research data into logical sections with detailed content. You MUST include relevant sources as citations in each section."
            },
            {
                "role": "user",
                "content": f"""Today's date is {datetime.now().strftime('%d/%m/%Y')}.
Query or Topic: {query}
Research data: {context}
Sources: {formatted_sources}
Citations: {citations}

Your task is to organize this research data into 3-5 logical sections with appropriate headers.
Each section should be comprehensive and detailed, with a minimum of 300 words per section.

IMPORTANT: You MUST include relevant sources in the content as markdown hyperlinks.
For example: 'This is a sample text. ([Source Title](url))'

For each major claim or piece of information, include a citation to the relevant source.
If a source doesn't have a URL, cite it by title.

Make sure each section covers a distinct aspect of the research topic and provides in-depth analysis.
The sections should flow logically and cover the topic comprehensively.

You MUST return nothing but a JSON array of section objects, each with a 'title' and 'content' field.
For example:
[
  {{
    "title": "Section Title 1",
    "content": "Detailed section content with sources..."
  }},
  {{
    "title": "Section Title 2",
    "content": "More detailed section content with sources..."
  }}
]
"""
            }
        ]
        
        # Call the model to generate sections
        response = await call_model(
            prompt,
            model,
            response_format="json",
        )
        
        # Handle potential errors
        if not response or not isinstance(response, list):
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "error",
                    "Error generating sections. Using default empty structure.",
                    self.websocket,
                )
            else:
                print_agent_output(
                    "Error generating sections. Using default empty structure.",
                    agent="SECTION_WRITER",
                )
            return []
            
        return response
        
    async def transform_to_research_data(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform sections to research_data format expected by the writer agent.
        
        Args:
            sections: List of section objects with title and content
            
        Returns:
            List of research_data items in the format expected by the writer agent
        """
        research_data = []
        
        for section in sections:
            if isinstance(section, dict) and "title" in section and "content" in section:
                research_data.append({
                    section["title"]: section["content"]
                })
                
        return research_data
        
    async def run(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the section writer agent.
        
        Args:
            research_state: Research state containing deep research data
            
        Returns:
            Transformed research state with sections as research_data
        """
        # Generate sections from deep research data
        sections = await self.generate_sections(research_state)
        
        # Transform sections to research_data format
        research_data = await self.transform_to_research_data(sections)
        
        # If no sections were generated, use the original research data
        if not research_data:
            research_data = research_state.get("research_data", [])
        
        # Preserve the formatted_sources if they exist
        formatted_sources = research_state.get("formatted_sources", [])
        
        # Return the transformed research state
        return {
            **research_state,
            "research_data": research_data,
            "sections": sections,  # Store the original sections for later use
            "formatted_sources": formatted_sources  # Preserve formatted sources
        } 