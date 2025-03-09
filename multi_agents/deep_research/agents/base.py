import logging
from typing import List, Dict, Any, Set, Optional
from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportType, ReportSource, Tone
from ...agents.utils.views import print_agent_output

logger = logging.getLogger(__name__)

# Maximum words allowed in context (100k words for larger research contexts)
MAX_CONTEXT_WORDS = 100000

def count_words(text: str) -> int:
    """Count words in a text string"""
    return len(text.split())

def trim_context_to_word_limit(context, max_words: int = MAX_CONTEXT_WORDS) -> str:
    """
    Trim context to stay within word limit while preserving most recent/relevant items.
    
    Args:
        context: Either a string or a list of strings to trim
        max_words: Maximum number of words to include
        
    Returns:
        A trimmed string
    """
    # Handle different input types
    if isinstance(context, str):
        # If input is a string, convert to list of paragraphs
        context_list = context.split("\n\n")
    elif isinstance(context, list):
        # If input is already a list, use as is
        context_list = context
    else:
        # For any other type, convert to string and then split
        context_list = str(context).split("\n\n")
    
    total_words = 0
    trimmed_context = []
    
    # Process in reverse to keep most recent items
    for item in reversed(context_list):
        words = count_words(item)
        if total_words + words <= max_words:
            trimmed_context.insert(0, item)  # Insert at start to maintain original order
            total_words += words
        else:
            break
    
    # Join the trimmed context items into a single string
    return "\n\n".join(trimmed_context)

class ResearchProgress:
    """Track progress of deep research"""
    def __init__(self, total_depth: int, total_breadth: int):
        self.current_depth = 1  # Start from 1 and increment up to total_depth
        self.total_depth = total_depth
        self.current_breadth = 0  # Start from 0 and count up to total_breadth as queries complete
        self.total_breadth = total_breadth
        self.current_query: Optional[str] = None
        self.total_queries = 0
        self.completed_queries = 0

class DeepResearchAgent:
    """Base agent for deep research operations"""
    def __init__(self, websocket=None, stream_output=None, tone=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.tone = tone or Tone.Objective
        self.headers = headers or {}
        
    async def _stream_or_print(self, message: str, agent_type: str = "RESEARCHER"):
        """Stream output to websocket or print to console"""
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "deep_research", message, self.websocket)
        else:
            print_agent_output(message, agent=agent_type)
            
    async def basic_research(self, query: str, verbose: bool = True, source: str = "web") -> tuple:
        """Conduct basic research using GPTResearcher"""
        researcher = GPTResearcher(
            query=query,
            report_type=ReportType.ResearchReport.value,
            report_source=source,
            tone=self.tone,
            websocket=self.websocket,
            headers=self.headers
        )
        
        # Conduct research
        context = await researcher.conduct_research()
        return context, researcher.visited_urls, researcher.research_sources
        
    async def search(self, query: str, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for information on a query.
        
        Args:
            query: The search query
            task: Task configuration
            
        Returns:
            List of search results
        """
        # Log the action
        await self._stream_or_print(f"Searching for information on: {query}", "RESEARCHER")
        
        # Get the source from task or use default
        source = task.get("source", "web")
        
        # Conduct basic research
        context, visited_urls, sources = await self.basic_research(
            query=query,
            source=source
        )
        
        # Debug log the research results
        print_agent_output(f"Basic research returned: {len(sources)} sources and {len(context) if context else 0} chars of context", "RESEARCHER")
        
        # Format search results
        search_results = []
        
        # Add sources with content
        for i, source in enumerate(sources):
            if isinstance(source, dict):
                # Debug log each source
                source_keys = ', '.join(source.keys())
                
                # Ensure the source has content
                if "content" not in source or not source["content"]:
                    # Try to extract content from other fields
                    for field in ["text", "snippet", "body", "description"]:
                        if field in source and source[field]:
                            source["content"] = source[field]
                            break
                
                # If still no content, create content from available fields
                if "content" not in source or not source["content"]:
                    content_parts = []
                    for key, value in source.items():
                        if key not in ["title", "url"] and isinstance(value, str) and len(value) > 10:
                            content_parts.append(f"{key}: {value}")
                    
                    if content_parts:
                        source["content"] = "\n".join(content_parts)
                
                search_results.append(source)
                
        # If no sources with content, create a result from context
        if not search_results and context:
            print_agent_output(f"No sources with content found. Creating a result from context ({len(context)} chars)", "RESEARCHER")
            search_results.append({
                "title": f"Research on {query}",
                "url": "",
                "content": context
            })
        
        # If still no search results, create a minimal result
        if not search_results:
            print_agent_output("No search results or context found. Creating a minimal result.", "RESEARCHER")
            search_results.append({
                "title": f"Research on {query}",
                "url": "",
                "content": f"No specific information found for the query: {query}. This could be due to API limitations, network issues, or lack of relevant information."
            })
            
        # Debug log the final search results
        print_agent_output(f"Returning {len(search_results)} search results", "RESEARCHER")
            
        return search_results 