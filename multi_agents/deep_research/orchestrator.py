import os
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta

from langgraph.graph import StateGraph, END
from ..agents.utils.views import print_agent_output
from ..agents.utils.utils import sanitize_filename

from .memory import DeepResearchState
from .agents import (
    DeepResearchAgent,
    DeepExplorerAgent,
    DeepSynthesizerAgent,
    DeepReviewerAgent
)

logger = logging.getLogger(__name__)

class DeepResearchOrchestrator:
    """Orchestrator for deep research using LangGraph"""
    
    def __init__(self, task: dict, websocket=None, stream_output=None, tone=None, headers=None):
        self.task = task
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}
        self.tone = tone
        self.task_id = self._generate_task_id()
        self.output_dir = self._create_output_directory()
        
        # Research parameters
        self.breadth = task.get('deep_research_breadth', 4)
        self.depth = task.get('deep_research_depth', 2)
        self.concurrency_limit = task.get('deep_research_concurrency', 2)
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
    def _generate_task_id(self):
        """Generate a unique task ID"""
        return int(time.time())
        
    def _create_output_directory(self):
        """Create output directory for research results"""
        output_dir = "./outputs/" + sanitize_filename(
            f"deep_research_{self.task_id}_{self.task.get('query')[0:40]}")
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
        
    def _initialize_agents(self):
        """Initialize all agents needed for deep research"""
        return {
            "explorer": DeepExplorerAgent(self.websocket, self.stream_output, self.tone, self.headers),
            "researcher": DeepResearchAgent(self.websocket, self.stream_output, self.tone, self.headers),
            "synthesizer": DeepSynthesizerAgent(self.websocket, self.stream_output, self.tone, self.headers),
            "reviewer": DeepReviewerAgent(self.websocket, self.stream_output, self.tone, self.headers)
        }
        
    async def _log_research_start(self):
        """Log the start of the research process"""
        message = f"Starting deep research process for query '{self.task.get('query')}'..."
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "starting_deep_research", message, self.websocket)
        else:
            print_agent_output(message, "MASTER")
            
    async def _on_progress(self, state: DeepResearchState):
        """Progress callback for deep research"""
        message = (f"Deep Research Progress: Depth {state.current_depth}/{state.total_depth}, "
                  f"Breadth {state.current_breadth}/{state.total_breadth}")
        
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "deep_research_progress", message, self.websocket)
        else:
            print_agent_output(message, "MASTER")
            
    async def generate_search_queries(self, state: DeepResearchState) -> DeepResearchState:
        """Generate search queries for research"""
        explorer = self.agents["explorer"]
        queries = await explorer.generate_search_queries(state.query, num_queries=state.breadth)
        state.set_search_queries(queries)
        return state
        
    async def generate_research_plan(self, state: DeepResearchState) -> DeepResearchState:
        """Generate research plan with follow-up questions"""
        explorer = self.agents["explorer"]
        plan = await explorer.generate_research_plan(state.query, num_questions=3)
        state.set_research_plan(plan)
        return state
        
    async def process_query(self, state: DeepResearchState, query_index: int) -> DeepResearchState:
        """Process a single search query"""
        if query_index >= len(state.search_queries):
            return state
            
        query_data = state.search_queries[query_index]
        query = query_data['query']
        
        # Update progress
        state.current_breadth = query_index + 1
        await self._on_progress(state)
        
        # Conduct basic research
        researcher = self.agents["researcher"]
        context, visited_urls, sources = await researcher.basic_research(
            query=query,
            verbose=self.task.get('verbose', True),
            source=self.task.get('source', 'web')
        )
        
        # Process research results
        synthesizer = self.agents["synthesizer"]
        results = await synthesizer.process_research_results(query, context)
        
        # Update state with results
        for learning in results['learnings']:
            citation = results['citations'].get(learning, '')
            state.add_learning(learning, citation)
            
        state.add_context(context)
        state.add_visited_urls(visited_urls)
        state.add_sources(sources)
        state.set_follow_up_questions(results['followUpQuestions'])
        
        return state
        
    async def process_all_queries(self, state: DeepResearchState) -> DeepResearchState:
        """Process all search queries with concurrency limit"""
        semaphore = asyncio.Semaphore(self.concurrency_limit)
        
        async def process_with_semaphore(index):
            async with semaphore:
                return await self.process_query(state, index)
                
        # Create tasks for all queries
        tasks = [process_with_semaphore(i) for i in range(len(state.search_queries))]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # Merge results (the state is shared, so we just need the final state)
        return results[-1] if results else state
        
    async def review_research(self, state: DeepResearchState) -> DeepResearchState:
        """Review research results"""
        reviewer = self.agents["reviewer"]
        review = await reviewer.review_research(state.query, state.learnings, state.citations)
        state.set_review(review)
        return state
        
    async def recursive_research(self, state: DeepResearchState) -> DeepResearchState:
        """Recursively conduct deeper research based on follow-up questions"""
        # Base case: if we've reached the maximum depth, return the current state
        if state.current_depth >= state.total_depth:
            return state
            
        # Increment depth
        state.current_depth += 1
        await self._on_progress(state)
        
        # Create a new query from follow-up questions
        if not state.follow_up_questions:
            return state
            
        new_query = f"""
        Original query: {state.query}
        Follow-up questions: {' '.join(state.follow_up_questions)}
        """
        
        # Create a new state for the next level
        new_state = DeepResearchState(
            task=state.task,
            query=new_query,
            breadth=max(2, state.breadth // 2),  # Reduce breadth for deeper levels
            depth=state.depth,
            current_depth=state.current_depth,
            total_depth=state.total_depth,
            learnings=state.learnings.copy(),
            citations=state.citations.copy(),
            visited_urls=state.visited_urls.copy(),
            context=state.context.copy(),
            sources=state.sources.copy()
        )
        
        # Generate new search queries
        new_state = await self.generate_search_queries(new_state)
        
        # Process all queries at this level
        new_state = await self.process_all_queries(new_state)
        
        # Merge results back to original state
        for learning in new_state.learnings:
            if learning not in state.learnings:
                state.add_learning(learning, new_state.citations.get(learning))
                
        for context_item in new_state.context:
            if context_item not in state.context:
                state.add_context(context_item)
                
        state.add_visited_urls(list(new_state.visited_urls))
        state.add_sources(new_state.sources)
        
        # Continue recursion
        return await self.recursive_research(state)
        
    async def finalize_research(self, state: DeepResearchState) -> DeepResearchState:
        """Finalize research results"""
        # Finalize context
        try:
            state.finalize_context()
        except Exception as e:
            logger.error(f"Error finalizing context: {e}")
            # Fallback: join context items if finalize_context fails
            if hasattr(state, 'context') and isinstance(state.context, list):
                state.final_context = "\n".join(state.context)
            else:
                state.final_context = ""
        
        # Ensure final_context is set
        if not hasattr(state, 'final_context') or not state.final_context:
            state.final_context = ""
            
        return state
        
    def should_continue_recursion(self, state: DeepResearchState) -> str:
        """Determine if we should continue with recursive research"""
        if state.current_depth < state.total_depth:
            return "continue"
        else:
            return "finalize"
            
    def create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for deep research"""
        workflow = StateGraph(DeepResearchState)
        
        # Add nodes
        workflow.add_node("generate_queries", self.generate_search_queries)
        workflow.add_node("generate_plan", self.generate_research_plan)
        workflow.add_node("process_queries", self.process_all_queries)
        workflow.add_node("review_research", self.review_research)
        workflow.add_node("recursive_research", self.recursive_research)
        workflow.add_node("finalize_research", self.finalize_research)
        
        # Add edges
        workflow.add_edge("generate_queries", "generate_plan")
        workflow.add_edge("generate_plan", "process_queries")
        workflow.add_edge("process_queries", "review_research")
        
        # Add conditional edge for recursion
        workflow.add_conditional_edges(
            "review_research",
            self.should_continue_recursion,
            {
                "continue": "recursive_research",
                "finalize": "finalize_research"
            }
        )
        
        workflow.add_edge("recursive_research", "review_research")
        workflow.add_edge("finalize_research", END)
        
        # Set entry point
        workflow.set_entry_point("generate_queries")
        
        return workflow
        
    async def run(self) -> Dict[str, Any]:
        """Run the deep research process"""
        start_time = time.time()
        
        # Log start of research
        await self._log_research_start()
        
        # Create workflow
        workflow = self.create_workflow()
        chain = workflow.compile()
        
        # Initialize state
        initial_state = DeepResearchState(
            task=self.task,
            query=self.task.get('query'),
            breadth=self.breadth,
            depth=self.depth,
            total_depth=self.depth
        )
        
        # Run the workflow
        config = {
            "configurable": {
                "thread_id": self.task_id,
                "thread_ts": datetime.utcnow()
            }
        }
        
        final_state = await chain.ainvoke(initial_state, config=config)
        
        # Log completion
        end_time = time.time()
        execution_time = timedelta(seconds=end_time - start_time)
        logger.info(f"Total deep research execution time: {execution_time}")
        
        # Return results
        return {
            "task": self.task,
            "query": self.task.get('query'),
            "context": getattr(final_state, 'final_context', '\n'.join(final_state.context) if hasattr(final_state, 'context') else ''),
            "learnings": getattr(final_state, 'learnings', []),
            "citations": getattr(final_state, 'citations', {}),
            "visited_urls": list(getattr(final_state, 'visited_urls', set())),
            "sources": getattr(final_state, 'sources', []),
            "review": getattr(final_state, 'review', None),
            "execution_time": str(execution_time)
        } 