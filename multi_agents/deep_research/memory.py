from typing import Dict, List, Any, Set, Optional
from pydantic import BaseModel, Field

class DeepResearchState(BaseModel):
    """State for deep research process"""
    # Task configuration
    task: Dict[str, Any] = Field(default_factory=dict)
    
    # Research parameters
    query: str = ""
    breadth: int = 4
    depth: int = 2
    
    # Research progress
    current_depth: int = 1
    total_depth: int = 2
    current_breadth: int = 0
    total_breadth: int = 4
    
    # Research results
    learnings: List[str] = Field(default_factory=list)
    citations: Dict[str, str] = Field(default_factory=dict)
    visited_urls: Set[str] = Field(default_factory=set)
    context: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Intermediate results
    search_queries: List[Dict[str, str]] = Field(default_factory=list)
    research_plan: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    
    # Review results
    review: Optional[Dict[str, Any]] = None
    
    # Final output
    final_context: str = ""
    
    def update_progress(self, depth: int, breadth: int):
        """Update research progress"""
        self.current_depth = depth
        self.current_breadth = breadth
        
    def add_learning(self, learning: str, citation: Optional[str] = None):
        """Add a learning with optional citation"""
        if learning not in self.learnings:
            self.learnings.append(learning)
            if citation:
                self.citations[learning] = citation
                
    def add_context(self, context: str):
        """Add context to the research state"""
        # Skip empty context
        if not context:
            return
            
        # Add context if it's not already in the list
        if context not in self.context:
            self.context.append(context)
            
    def add_visited_urls(self, urls: List[str]):
        """Add visited URLs to the research state"""
        for url in urls:
            self.visited_urls.add(url)
            
    def add_sources(self, sources: List[Dict[str, Any]]):
        """Add sources to the research state"""
        for source in sources:
            if source not in self.sources:
                self.sources.append(source)
                
    def set_search_queries(self, queries: List[Dict[str, str]]):
        """Set search queries"""
        self.search_queries = queries
        self.total_breadth = len(queries)
        
    def set_research_plan(self, plan: List[str]):
        """Set research plan"""
        self.research_plan = plan
        
    def set_follow_up_questions(self, questions: List[str]):
        """Set follow-up questions"""
        self.follow_up_questions = questions
        
    def set_review(self, review: Dict[str, Any]):
        """Set review results"""
        self.review = review
        
    def finalize_context(self):
        """Finalize context for report generation"""
        from .agents.base import trim_context_to_word_limit
        
        # Prepare context with citations
        context_with_citations = []
        
        # Add learnings with citations
        for learning in self.learnings:
            citation = self.citations.get(learning, '')
            if citation:
                context_with_citations.append(f"{learning} [Source: {citation}]")
            else:
                context_with_citations.append(learning)
        
        # Add all research context
        if self.context:
            context_with_citations.extend(self.context)
        
        # Add source content with proper attribution
        for source in self.sources:
            if isinstance(source, dict):
                title = source.get("title", "Unknown Title")
                url = source.get("url", "")
                content = source.get("content", "")
                if content:
                    context_with_citations.append(f"From {title} [{url}]: {content}")
        
        # Trim final context to word limit
        final_context_list = trim_context_to_word_limit(context_with_citations)
        self.final_context = "\n".join(final_context_list)
        
        return self.final_context 