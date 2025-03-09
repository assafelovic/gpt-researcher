"""
Reporter Agent for Deep Research

This agent is responsible for formatting the report for the publisher agent.
"""

from typing import Dict, Any, List

from ...agents.utils.views import print_agent_output
from .base import DeepResearchAgent

class ReporterAgent(DeepResearchAgent):
    """
    Agent responsible for formatting the report for the publisher agent.
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
        
    def extract_sections_from_research_data(self, research_data: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Extract sections from research_data.
        
        Args:
            research_data: List of research_data items
            
        Returns:
            List of section objects with title and content
        """
        sections = []
        
        for item in research_data:
            for title, content in item.items():
                sections.append({
                    "title": title,
                    "content": content
                })
                
        return sections
        
    async def prepare_publisher_state(self, writer_output: Dict[str, Any], research_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the state for the publisher agent.
        
        Args:
            writer_output: Output from the writer agent
            research_state: Original research state
            
        Returns:
            State for the publisher agent
        """
        # Log the action
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "formatting_report",
                f"Formatting report for publisher...",
                self.websocket,
            )
        else:
            print_agent_output(
                f"Formatting report for publisher...",
                agent="REPORTER",
            )
            
        # Use sections from research_state if available, otherwise extract from research_data
        if "sections" in research_state and research_state["sections"]:
            sections = research_state["sections"]
        else:
            sections = self.extract_sections_from_research_data(research_state.get("research_data", []))
        
        # Validate that sections exist
        if not sections:
            error_msg = "No sections found in research data. Cannot format report."
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "error",
                    error_msg,
                    self.websocket,
                )
            else:
                print_agent_output(
                    error_msg,
                    agent="REPORTER",
                )
            raise ValueError(error_msg)
            
        # Format sources for references
        sources = research_state.get("sources", [])
        formatted_sources = []
        
        # Extract URLs from sections to ensure all cited sources are included
        cited_urls = set()
        for section in sections:
            if isinstance(section, dict) and "content" in section:
                content = section["content"]
                # Find all URLs in markdown format
                import re
                urls = re.findall(r'\[.*?\]\((https?://[^\s\)]+)\)', content)
                for url in urls:
                    cited_urls.add(url)
        
        # Ensure sources are properly formatted and include all cited URLs
        for source in sources:
            if isinstance(source, dict) and "url" in source:
                # Format source as a reference
                title = source.get("title", "Unknown Title")
                url = source.get("url", "")
                formatted_sources.append(f"- {title} [{url}]({url})")
                # Remove from cited_urls if present
                if url in cited_urls:
                    cited_urls.remove(url)
            elif isinstance(source, str):
                # Source is already a string
                formatted_sources.append(source)
        
        # Add any remaining cited URLs that weren't in the sources
        for url in cited_urls:
            formatted_sources.append(f"- Additional Source [{url}]({url})")
        
        # Validate that we have sources
        if not formatted_sources:
            error_msg = "No sources found for research. Cannot format report without sources."
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "error",
                    error_msg,
                    self.websocket,
                )
            else:
                print_agent_output(
                    error_msg,
                    agent="REPORTER",
                )
            raise ValueError(error_msg)
            
        # Return the publisher state
        return {
            "task": research_state.get("task", {}),
            "headers": writer_output.get("headers", {}),
            "research_data": research_state.get("research_data", []),
            "sources": formatted_sources,
            "introduction": writer_output.get("introduction", ""),
            "conclusion": writer_output.get("conclusion", ""),
            "table_of_contents": writer_output.get("table_of_contents", ""),
            "title": research_state.get("title", ""),
            "date": research_state.get("date", ""),
            "sections": sections  # Explicitly include sections
        }
        
    async def run(self, writer_output: Dict[str, Any], research_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the reporter agent.
        
        Args:
            writer_output: Output from the writer agent
            research_state: Original research state
            
        Returns:
            State for the publisher agent
        """
        return await self.prepare_publisher_state(writer_output, research_state) 