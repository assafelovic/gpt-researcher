from typing import Dict, List, Any, Set, Optional, Annotated
from pydantic import BaseModel, Field
from .agents.base import trim_context_to_word_limit

# Define our own merge_dicts function since it's not available in the current langgraph version
def merge_dicts(old_dict: Dict, new_dict: Dict) -> Dict:
    """Merge two dictionaries, updating the old_dict with values from new_dict."""
    result = old_dict.copy()
    result.update(new_dict)
    return result

# Define our own append_list function since it's not available in the current langgraph version
def append_list(old_list: List, new_list: List) -> List:
    """Append items from new_list to old_list, avoiding duplicates."""
    result = old_list.copy()
    for item in new_list:
        if item not in result:
            result.append(item)
    return result

class DeepResearchState(BaseModel):
    """
    State for deep research process.
    
    Key context-related attributes:
    - context_items: List of individual research findings/context pieces collected during research
    - final_context: The final processed context string (only set at the end by the finalizer)
    """
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
    learnings: Annotated[List[str], append_list] = Field(default_factory=list)
    citations: Annotated[Dict[str, str], merge_dicts] = Field(default_factory=dict)
    visited_urls: Annotated[Set[str], lambda x, y: x.union(y)] = Field(default_factory=set)
    
    # Primary context storage - individual pieces of research
    context_items: Annotated[List[str], append_list] = Field(default_factory=list)
    
    # Legacy context field - kept for backward compatibility
    context: Annotated[List[str], append_list] = Field(default_factory=list)
    
    # Sources from research
    sources: Annotated[List[Dict[str, Any]], append_list] = Field(default_factory=list)
    
    # Intermediate results
    search_queries: List[Dict[str, str]] = Field(default_factory=list)
    research_plan: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    
    # Review results
    review: Optional[Dict[str, Any]] = None
    
    # Final output - set by the finalizer
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
        """Add context to the research state (legacy method)"""
        # Skip empty context
        if not context:
            return
            
        # Add context if it's not already in the list
        if context not in self.context:
            self.context.append(context)
            
    def add_context_item(self, context_item: str):
        """Add a context item to the research state"""
        # Skip empty context items
        if not context_item:
            return
            
        # Add context item if it's not already in the list
        if context_item not in self.context_items:
            self.context_items.append(context_item)
            
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
        """
        Finalize context for report generation.
        
        This method combines all context_items into a single string,
        trims it to a reasonable size, and returns it.
        """
        
        # Combine all context items
        combined_context = "\n\n".join(self.context_items)
        
        # If no context items, try using legacy context
        if not combined_context and self.context:
            combined_context = "\n\n".join(self.context)
            
        # If still no context, create a default message
        if not combined_context:
            combined_context = f"Research on: {self.query}\n\nNo specific research data was collected."
        
        # Trim the combined context to a reasonable size
        trimmed_context = trim_context_to_word_limit(combined_context)
        
        # Set and return the final context
        self.final_context = trimmed_context
        return self.final_context 