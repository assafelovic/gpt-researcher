"""
Report Formatter Agent for Deep Research

This agent is responsible for formatting the report for the publisher agent.
"""

from typing import Dict, Any, List

from ...agents.utils.views import print_agent_output
from .base import DeepResearchAgent

class ReportFormatterAgent(DeepResearchAgent):
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
                agent="REPORT_FORMATTER",
            )
            
        # Use sections from research_state if available, otherwise extract from research_data
        if "sections" in research_state and research_state["sections"]:
            sections = research_state["sections"]
        else:
            sections = self.extract_sections_from_research_data(research_state.get("research_data", []))
            
        # Format sources for references
        sources = research_state.get("sources", [])
        formatted_sources = []
        
        # Ensure sources are properly formatted
        for source in sources:
            if isinstance(source, dict) and "url" in source:
                # Format source as a reference
                title = source.get("title", "Unknown Title")
                url = source.get("url", "")
                formatted_sources.append(f"- {title} [{url}]({url})")
            elif isinstance(source, str):
                # Source is already a string
                formatted_sources.append(source)
                
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
        Run the report formatter agent.
        
        Args:
            writer_output: Output from the writer agent
            research_state: Original research state
            
        Returns:
            State for the publisher agent
        """
        return await self.prepare_publisher_state(writer_output, research_state) 