import logging
from typing import List, Dict, Any, Set, Optional
from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportType, ReportSource, Tone
from ...agents.utils.views import print_agent_output

logger = logging.getLogger(__name__)

# Maximum words allowed in context (25k words for safety margin)
MAX_CONTEXT_WORDS = 25000

def count_words(text: str) -> int:
    """Count words in a text string"""
    return len(text.split())

def trim_context_to_word_limit(context_list: List[str], max_words: int = MAX_CONTEXT_WORDS) -> List[str]:
    """Trim context list to stay within word limit while preserving most recent/relevant items"""
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
            
    return trimmed_context

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