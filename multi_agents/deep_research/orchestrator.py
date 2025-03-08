import os
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta

from langgraph.graph import StateGraph, END
from ..agents.utils.views import print_agent_output, AgentColor
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
            
    async def _on_progress(self, state: DeepResearchState, current_depth=None, current_breadth=None, total_breadth=None):
        """Progress callback for deep research"""
        # Use provided values or get from state
        current_depth = current_depth if current_depth is not None else state.current_depth
        current_breadth = current_breadth if current_breadth is not None else state.current_breadth
        total_breadth = total_breadth if total_breadth is not None else state.total_breadth
        
        message = (f"Deep Research Progress: Depth {current_depth}/{state.total_depth}, "
                  f"Breadth {current_breadth}/{total_breadth}")
        
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "deep_research_progress", message, self.websocket)
        else:
            print_agent_output(message, "MASTER")
            
    async def generate_search_queries(self, state: DeepResearchState) -> dict:
        """Generate search queries for research"""
        explorer = self.agents["explorer"]
        queries = await explorer.generate_search_queries(state.query, num_queries=state.breadth)
        
        # Return a dictionary with updated search queries
        return {
            "search_queries": queries,
            "total_breadth": len(queries)
        }
        
    async def generate_research_plan(self, state: DeepResearchState) -> dict:
        """Generate a research plan based on search queries"""
        explorer = self.agents["explorer"]
        
        # Extract query titles for planning
        query_titles = [q.get("title", q.get("query", "")) for q in state.search_queries]
        
        # Generate research plan
        plan = await explorer.generate_research_plan(state.query, query_titles)
        
        # Return a dictionary with updated research plan
        return {
            "research_plan": plan
        }
        
    async def process_query(self, state: DeepResearchState, query_index: int) -> dict:
        """Process a single search query"""
        if query_index >= len(state.search_queries):
            return {}
            
        # Get the query to process
        query_data = state.search_queries[query_index]
        query_text = query_data.get("query", "")
        query_title = query_data.get("title", query_text)
        
        # Calculate current progress
        current_breadth = query_index + 1
        total_breadth = len(state.search_queries)
        
        # Log the action
        message = f"Processing query {current_breadth}/{total_breadth}: {query_title}"
        await self._on_progress(state, current_breadth=current_breadth, total_breadth=total_breadth)
        
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "processing_query",
                message,
                self.websocket,
            )
        else:
            print_agent_output(
                message,
                agent="RESEARCHER",
            )
            
        # Conduct research
        researcher = self.agents["researcher"]
        context, visited_urls, sources = await researcher.basic_research(
            query=query_text,
            source=self.task.get("source", "web")
        )
        
        # Process research results
        synthesizer = self.agents["synthesizer"]
        learnings, citations = await synthesizer.process_research_results(
            query=query_text,
            context=context
        )
        
        # Generate follow-up questions if this is the first query
        follow_up_questions = []
        if query_index == 0 and not state.follow_up_questions:
            explorer = self.agents["explorer"]
            follow_up_questions = await explorer.generate_follow_up_questions(
                query=state.query,
                context=context,
                num_questions=3
            )
            
            # Log the follow-up questions
            if follow_up_questions:
                questions_str = "\n".join([f"- {q}" for q in follow_up_questions])
                log_message = f"Generated follow-up questions:\n{questions_str}"
                
                if self.websocket and self.stream_output:
                    await self.stream_output(
                        "logs",
                        "follow_up_questions",
                        log_message,
                        self.websocket,
                    )
                else:
                    print_agent_output(
                        log_message,
                        agent="EXPLORER",
                    )
        
        # Update state with new information
        new_learnings = []
        new_citations = {}
        
        for learning in learnings:
            if learning not in state.learnings:
                new_learnings.append(learning)
                if learning in citations:
                    new_citations[learning] = citations[learning]
                
        # Return a dictionary with updated values
        result = {
            "current_breadth": query_index + 1,
            "learnings": state.learnings + new_learnings,
            "citations": {**state.citations, **new_citations},
            "visited_urls": state.visited_urls.union(visited_urls),
            "context": state.context + [context] if context else state.context,
            "sources": state.sources + sources if sources else state.sources
        }
        
        # Add follow-up questions if generated
        if follow_up_questions:
            result["follow_up_questions"] = follow_up_questions
            
        return result
        
    async def process_all_queries(self, state: DeepResearchState) -> dict:
        """Process all search queries with concurrency control"""
        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.concurrency_limit)
        
        # Define a function to process a query with the semaphore
        async def process_with_semaphore(index):
            async with semaphore:
                return await self.process_query(state, index)
        
        # Process queries concurrently with semaphore control
        tasks = [process_with_semaphore(i) for i in range(len(state.search_queries))]
        results = await asyncio.gather(*tasks)
        
        # Combine all results
        combined_learnings = state.learnings.copy()
        combined_citations = state.citations.copy()
        combined_visited_urls = state.visited_urls.copy()
        combined_context = state.context.copy()
        combined_sources = state.sources.copy()
        combined_follow_up_questions = state.follow_up_questions.copy()
        
        for result in results:
            if result:  # Skip empty results
                # Add learnings and citations
                new_learnings = result.get("learnings", [])
                for i, learning in enumerate(new_learnings):
                    if learning not in combined_learnings:
                        combined_learnings.append(learning)
                
                # Update citations
                combined_citations.update(result.get("citations", {}))
                
                # Update visited URLs
                combined_visited_urls = combined_visited_urls.union(result.get("visited_urls", set()))
                
                # Update context
                new_context = result.get("context", [])
                for ctx in new_context:
                    if ctx and ctx not in combined_context:
                        combined_context.append(ctx)
                
                # Update sources
                new_sources = result.get("sources", [])
                for source in new_sources:
                    if source and source not in combined_sources:
                        combined_sources.append(source)
                
                # Update follow-up questions
                new_follow_up_questions = result.get("follow_up_questions", [])
                for question in new_follow_up_questions:
                    if question and question not in combined_follow_up_questions:
                        combined_follow_up_questions.append(question)
        
        # Log completion of all queries
        total_breadth = len(state.search_queries)
        await self._on_progress(state, current_breadth=total_breadth, total_breadth=total_breadth)
        
        # Return a dictionary with all updated values
        return {
            "current_breadth": total_breadth,
            "learnings": combined_learnings,
            "citations": combined_citations,
            "visited_urls": combined_visited_urls,
            "context": combined_context,
            "sources": combined_sources,
            "follow_up_questions": combined_follow_up_questions
        }
        
    async def review_research(self, state: DeepResearchState) -> dict:
        """Review research results"""
        reviewer = self.agents["reviewer"]
        review = await reviewer.review_research(state.query, state.learnings, state.citations)
        
        # Return a dictionary with the review
        return {
            "review": review
        }
        
    async def recursive_research(self, state: DeepResearchState) -> dict:
        """Recursively conduct deeper research based on follow-up questions"""
        # Base case: if we've reached the maximum depth, return the current state
        if state.current_depth >= state.total_depth:
            return {}
            
        # Increment depth
        current_depth = state.current_depth + 1
        await self._on_progress(state, current_depth=current_depth)
        
        # Create a new query from follow-up questions
        if not state.follow_up_questions:
            return {}
            
        new_query = f"""
        Original query: {state.query}
        Follow-up questions: {' '.join(state.follow_up_questions)}
        """
        
        # Create a temporary state for the next level
        temp_state = DeepResearchState(
            task=state.task,
            query=new_query,
            breadth=max(2, state.breadth // 2),  # Reduce breadth for deeper levels
            depth=state.depth,
            current_depth=current_depth,
            total_depth=state.total_depth,
            learnings=state.learnings.copy(),
            citations=state.citations.copy(),
            visited_urls=state.visited_urls.copy(),
            context=state.context.copy(),
            sources=state.sources.copy()
        )
        
        # Generate new search queries
        queries_result = await self.generate_search_queries(temp_state)
        temp_state.search_queries = queries_result.get("search_queries", [])
        temp_state.total_breadth = queries_result.get("total_breadth", 0)
        
        # Process all queries at this level
        process_result = await self.process_all_queries(temp_state)
        
        # Merge results
        new_learnings = []
        new_citations = {}
        new_context = []
        new_sources = []
        
        # Get new learnings and citations
        for learning in process_result.get("learnings", []):
            if learning not in state.learnings:
                new_learnings.append(learning)
                citation = process_result.get("citations", {}).get(learning)
                if citation:
                    new_citations[learning] = citation
        
        # Get new context
        for ctx in process_result.get("context", []):
            if ctx not in state.context:
                new_context.append(ctx)
                
        # Get new sources
        for source in process_result.get("sources", []):
            if source not in state.sources:
                new_sources.append(source)
                
        # Return a dictionary with all updated values
        return {
            "current_depth": current_depth,
            "learnings": state.learnings + new_learnings,
            "citations": {**state.citations, **new_citations},
            "visited_urls": state.visited_urls.union(process_result.get("visited_urls", set())),
            "context": state.context + new_context,
            "sources": state.sources + new_sources
        }
        
    async def finalize_research(self, state: DeepResearchState) -> dict:
        """Finalize research and prepare for report generation"""
        # Log the action
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "finalizing_research",
                f"Finalizing research...",
                self.websocket,
            )
        else:
            print_agent_output(
                f"Finalizing research...",
                agent="ORCHESTRATOR",
            )
            
        # The context already contains the research results with sources
        # We don't need to check for empty sources as the context itself is the source
        # Just ensure the context is not empty
        if not state.context:
            error_msg = "No research context collected. Cannot generate report without research data."
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
                    agent="ORCHESTRATOR",
                )
            raise ValueError(error_msg)
        
        # Finalize context by joining all context items
        final_context = state.finalize_context()
        
        # Return a dictionary with the final context
        return {
            "final_context": final_context
        }
        
    def should_continue_recursion(self, state: DeepResearchState) -> str:
        """Determine if we should continue with recursive research"""
        if state.current_depth < state.total_depth and state.follow_up_questions:
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
        
        # Extract values from the final state
        # The final state might be an AddableValuesDict or a DeepResearchState
        if hasattr(final_state, 'get'):
            # It's a dictionary-like object
            context = final_state.get('final_context', '')
            if not context and 'context' in final_state:
                # Try to join context if it's a list
                context_list = final_state.get('context', [])
                if isinstance(context_list, list):
                    context = '\n'.join(context_list)
                else:
                    context = str(context_list)
                    
            # Extract other values
            learnings = final_state.get('learnings', [])
            citations = final_state.get('citations', {})
            visited_urls = final_state.get('visited_urls', set())
            sources = final_state.get('sources', [])
            review = final_state.get('review', None)
        else:
            # It's a DeepResearchState object
            context = final_state.final_context if hasattr(final_state, 'final_context') else '\n'.join(final_state.context)
            learnings = final_state.learnings
            citations = final_state.citations
            visited_urls = final_state.visited_urls
            sources = final_state.sources
            review = final_state.review
        
        # Return results
        return {
            "task": self.task,
            "query": self.task.get('query'),
            "context": context,
            "learnings": learnings,
            "citations": citations,
            "visited_urls": list(visited_urls) if isinstance(visited_urls, set) else [],
            "sources": sources,
            "review": review,
            "execution_time": str(execution_time)
        } 