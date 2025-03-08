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
    DeepReviewerAgent,
    PlannerAgent,
    FinalizerAgent
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
            "reviewer": DeepReviewerAgent(self.websocket, self.stream_output, self.tone, self.headers),
            "planner": PlannerAgent(self.websocket, self.stream_output, self.tone, self.headers),
            "finalizer": FinalizerAgent(self.websocket, self.stream_output, self.tone, self.headers)
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
        """Generate search queries for research using the planner agent"""
        planner = self.agents["planner"]
        
        # Create a temporary state for the planner
        planner_state = {
            "query": state.query,
            "breadth": state.breadth
        }
        
        # Run the planner to generate search queries
        planner_result = await planner.run(planner_state)
        
        # Extract search queries and total breadth
        queries = planner_result.get("search_queries", [])
        total_breadth = planner_result.get("total_breadth", len(queries))
        
        # Return a dictionary with updated search queries
        return {
            "search_queries": queries,
            "total_breadth": total_breadth,
            "research_plan": planner_result.get("research_plan", "")
        }
        
    async def process_query(self, state: DeepResearchState, query_index: int) -> dict:
        """Process a single search query"""
        # Get the query
        if query_index >= len(state.search_queries):
            return {"error": f"Query index {query_index} out of range"}
            
        query_obj = state.search_queries[query_index]
        query = query_obj.get("query", "")
        title = query_obj.get("title", f"Query {query_index + 1}")
        
        # Log progress
        await self._on_progress(state, current_breadth=query_index+1)
        
        # Log the action
        message = f"Processing query {query_index + 1}/{state.total_breadth}: '{title}'"
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "processing_query", message, self.websocket)
        else:
            print_agent_output(message, "MASTER")
            
        # Get the researcher agent
        researcher = self.agents["researcher"]
        
        # Run the researcher agent to get search results
        print_agent_output(f"Searching for: '{query}'", "MASTER")
        
        try:
            search_results = await researcher.search(query, state.task)
            
            # Check if we have search results
            if not search_results:
                message = f"No search results found for query: '{title}'"
                if self.websocket and self.stream_output:
                    await self.stream_output("logs", "no_search_results", message, self.websocket)
                else:
                    print_agent_output(message, "MASTER")
                return {"context_item": "", "sources": [], "citations": {}}
                
            # Log search results
            print_agent_output(f"Found {len(search_results)} search results for query: '{title}'", "MASTER")
            
            # Get the synthesizer agent
            synthesizer = self.agents["synthesizer"]
            
            # Run the synthesizer agent to synthesize the search results
            print_agent_output(f"Synthesizing search results for query: '{title}'", "MASTER")
            
            synthesis_result = await synthesizer.synthesize(
                query=query,
                search_results=search_results,
                task=state.task
            )
            
            # Extract the context, sources, and citations
            context_item = synthesis_result.get("context", "")
            sources = synthesis_result.get("sources", [])
            citations = synthesis_result.get("citations", {})
            
            # Log synthesis results
            print_agent_output(
                f"Synthesis complete: {len(context_item)} chars context, {len(sources)} sources, {len(citations)} citations",
                "MASTER"
            )
            
            # If synthesis didn't return any context but we have search results, create a fallback
            if not context_item and search_results:
                print_agent_output(
                    "WARNING: Synthesis returned empty context despite having search results. Creating fallback context.",
                    "MASTER"
                )
                
                # Create a fallback context directly from the search results
                fallback_context = f"# Research on: {query}\n\n"
                
                # Add content from each search result
                for i, result in enumerate(search_results):
                    if isinstance(result, dict):
                        result_title = result.get("title", "Unknown Title")
                        url = result.get("url", "")
                        content = result.get("content", "")
                        
                        if result_title or url or content:
                            fallback_context += f"## Source {i+1}: {result_title}\n"
                            if url:
                                fallback_context += f"URL: {url}\n\n"
                            if content:
                                # Add a snippet of the content
                                snippet = content[:500] + "..." if len(content) > 500 else content
                                fallback_context += f"{snippet}\n\n"
                
                # Use the fallback context
                context_item = fallback_context
                sources = search_results
                
                print_agent_output(
                    f"Created fallback context: {len(context_item)} chars",
                    "MASTER"
                )
            
            # Return the results
            return {
                "context_item": context_item,
                "sources": sources,
                "citations": citations
            }
            
        except Exception as e:
            print_agent_output(f"Error processing query '{title}': {str(e)}", "MASTER")
            return {"error": f"Exception: {str(e)}"}
        
    async def process_all_queries(self, state: DeepResearchState) -> dict:
        """Process all search queries"""
        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.concurrency_limit)
        
        # Debug log the initial state
        print_agent_output(
            f"Starting process_all_queries with {len(state.search_queries)} queries, {len(state.context_items)} context items, and {len(state.sources)} sources.",
            "MASTER"
        )
        
        # Check if we have any search queries
        if not state.search_queries:
            print_agent_output(
                "WARNING: No search queries found. Cannot process queries without search queries.",
                "MASTER"
            )
            return {
                "context_items": state.context_items,
                "sources": state.sources,
                "citations": state.citations,
                "current_depth": state.current_depth
            }
        
        async def process_with_semaphore(index):
            """Process a query with semaphore for concurrency control"""
            async with semaphore:
                try:
                    result = await self.process_query(state, index)
                    # Debug log each query result
                    if "error" in result:
                        print_agent_output(f"Query {index} error: {result['error']}", "MASTER")
                    else:
                        context_item = result.get("context_item", "")
                        sources = result.get("sources", [])
                        print_agent_output(
                            f"Query {index} result: {len(context_item)} chars context, {len(sources)} sources",
                            "MASTER"
                        )
                    return result
                except Exception as e:
                    print_agent_output(f"Error processing query {index}: {str(e)}", "MASTER")
                    return {"error": f"Exception: {str(e)}"}
                
        # Create tasks for all queries
        tasks = [process_with_semaphore(i) for i in range(len(state.search_queries))]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # Combine results
        combined_context_items = list(state.context_items)  # Create a copy to avoid modifying the original
        combined_sources = list(state.sources)  # Create a copy
        combined_citations = dict(state.citations)  # Create a copy
        
        # Debug log the results before combining
        print_agent_output(
            f"Processing {len(results)} query results to combine",
            "MASTER"
        )
        
        # Track how many results actually contributed data
        results_with_context = 0
        results_with_sources = 0
        
        for i, result in enumerate(results):
            if "error" in result:
                # Skip errors
                print_agent_output(f"Skipping result {i} due to error", "MASTER")
                continue
                
            # Add context item
            context_item = result.get("context_item", "")
            if context_item:
                combined_context_items.append(context_item)
                results_with_context += 1
                print_agent_output(f"Added context item from result {i}: {len(context_item)} chars", "MASTER")
                
            # Add sources
            sources = result.get("sources", [])
            if sources:
                combined_sources.extend(sources)
                results_with_sources += 1
                print_agent_output(f"Added {len(sources)} sources from result {i}", "MASTER")
                
            # Add citations
            citations = result.get("citations", {})
            if citations:
                combined_citations.update(citations)
                print_agent_output(f"Added {len(citations)} citations from result {i}", "MASTER")
        
        # Log the results
        message = f"Collected {len(combined_context_items)} context items and {len(combined_sources)} sources."
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "collected_results", message, self.websocket)
        else:
            print_agent_output(message, "MASTER")
            
        # Debug log the final state
        print_agent_output(
            f"Ending process_all_queries with {len(combined_context_items)} context items and {len(combined_sources)} sources.",
            "MASTER"
        )
        
        # Debug log how many results contributed data
        print_agent_output(
            f"{results_with_context}/{len(results)} results contributed context items, {results_with_sources}/{len(results)} contributed sources",
            "MASTER"
        )
        
        # If we didn't collect any context items or sources, create a fallback
        if not combined_context_items and not combined_sources:
            print_agent_output(
                "WARNING: No context items or sources collected. Creating fallback context.",
                "MASTER"
            )
            
            # Create a fallback context
            fallback_context = f"Research on: {state.query}\n\n"
            fallback_context += "No specific research data was collected from the search queries. "
            fallback_context += "This could be due to API limitations, network issues, or lack of relevant information. "
            fallback_context += "Consider refining your search query or trying again later."
            
            # Add the fallback context
            combined_context_items.append(fallback_context)
        
        # Return combined results following LangGraph pattern
        return {
            "context_items": combined_context_items,
            "sources": combined_sources,
            "citations": combined_citations,
            "current_depth": state.current_depth  # Explicitly include current_depth
        }
        
    async def review_research(self, state: DeepResearchState) -> dict:
        """Review the research results and identify follow-up questions"""
        # Get the reviewer agent
        reviewer = self.agents["reviewer"]
        
        # Log the action
        message = f"Reviewing research results and identifying follow-up questions..."
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "reviewing_research", message, self.websocket)
        else:
            print_agent_output(message, "MASTER")
            
        # Run the reviewer agent
        review_result = await reviewer.review(
            query=state.query,
            context_items=state.context_items,
            current_depth=state.current_depth,
            total_depth=state.total_depth
        )
        
        # Extract follow-up questions
        follow_up_questions = review_result.get("follow_up_questions", [])
        
        # Return the results, including the current depth to ensure it's preserved
        return {
            "follow_up_questions": follow_up_questions,
            "current_depth": state.current_depth  # Explicitly include current_depth
        }
        
    async def recursive_research(self, state: DeepResearchState) -> dict:
        """Perform recursive research on follow-up questions"""
        # Log the action
        message = f"Starting recursive research at depth {state.current_depth + 1}..."
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "recursive_research", message, self.websocket)
        else:
            print_agent_output(message, "MASTER")
            
        # Get the follow-up questions
        follow_up_questions = state.follow_up_questions
        
        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.concurrency_limit)
        
        async def process_follow_up(question):
            """Process a follow-up question"""
            async with semaphore:
                # Log the action
                q_message = f"Researching follow-up question: '{question}'"
                if self.websocket and self.stream_output:
                    await self.stream_output("logs", "follow_up_question", q_message, self.websocket)
                else:
                    print_agent_output(q_message, "MASTER")
                    
                # Get the researcher agent
                researcher = self.agents["researcher"]
                
                # Run the researcher agent to get search results
                search_results = await researcher.search(question, state.task)
                
                # Check if we have search results
                if not search_results:
                    q_message = f"No search results found for follow-up question: '{question}'"
                    if self.websocket and self.stream_output:
                        await self.stream_output("logs", "no_search_results", q_message, self.websocket)
                    else:
                        print_agent_output(q_message, "MASTER")
                    return {"context_item": "", "sources": [], "citations": {}}
                    
                # Get the synthesizer agent
                synthesizer = self.agents["synthesizer"]
                
                # Run the synthesizer agent to synthesize the search results
                synthesis_result = await synthesizer.synthesize(
                    query=question,
                    search_results=search_results,
                    task=state.task
                )
                
                # Extract the context, sources, and citations
                context_item = synthesis_result.get("context", "")
                sources = synthesis_result.get("sources", [])
                citations = synthesis_result.get("citations", {})
                
                # Return the results
                return {
                    "context_item": context_item,
                    "sources": sources,
                    "citations": citations
                }
                
        # Create tasks for all follow-up questions
        tasks = [process_follow_up(q) for q in follow_up_questions]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # Combine results
        combined_context_items = list(state.context_items)  # Create a copy to avoid modifying the original
        combined_sources = list(state.sources)  # Create a copy
        combined_citations = dict(state.citations)  # Create a copy
        
        for result in results:
            # Add context item
            context_item = result.get("context_item", "")
            if context_item:
                combined_context_items.append(context_item)
                
            # Add sources
            sources = result.get("sources", [])
            if sources:
                combined_sources.extend(sources)
                
            # Add citations
            citations = result.get("citations", {})
            if citations:
                combined_citations.update(citations)
                
        # Return combined results with incremented depth following LangGraph pattern
        return {
            "context_items": combined_context_items,
            "sources": combined_sources,
            "citations": combined_citations,
            "current_depth": state.current_depth + 1
        }
        
    async def finalize_research(self, state: DeepResearchState) -> dict:
        """Finalize the research process using the finalizer agent"""
        finalizer = self.agents["finalizer"]
        
        # Create a temporary state for the finalizer
        finalizer_state = {
            "query": state.query,
            "context_items": state.context_items,
            "sources": state.sources,
            "citations": state.citations
        }
        
        # Run the finalizer to generate the final context
        finalizer_result = await finalizer.run(finalizer_state)
        
        # Return the finalized research state
        return {
            "context": finalizer_result.get("context", ""),
            "summary": finalizer_result.get("summary", ""),
            "sources": finalizer_result.get("sources", []),
            "citations": finalizer_result.get("citations", {}),
            "final_context": finalizer_result.get("final_context", "")
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
        workflow.add_node("process_queries", self.process_all_queries)
        workflow.add_node("review_research", self.review_research)
        workflow.add_node("recursive_research", self.recursive_research)
        workflow.add_node("finalize_research", self.finalize_research)
        
        # Add edges
        workflow.add_edge("generate_queries", "process_queries")
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
        # Log the start of the research process
        await self._log_research_start()
        
        # Create the workflow
        workflow = self.create_workflow()
        
        # Compile the workflow to get an executable chain
        chain = workflow.compile()
        
        # Create the initial state
        initial_state = DeepResearchState(
            query=self.task.get("query", ""),
            task=self.task,
            breadth=self.breadth,
            total_depth=self.depth,
            current_depth=1,  # Start at depth 1 to match DeepResearchState default
            total_breadth=0,
            search_queries=[],
            context_items=[],
            sources=[],
            citations={},
            follow_up_questions=[]
        )
        
        # Run the workflow with async invoke
        config = {
            "configurable": {
                "thread_id": self.task_id,
                "thread_ts": datetime.utcnow()
            }
        }
        
        try:
            result = await chain.ainvoke(initial_state, config=config)
            
            # Convert the result to a dictionary to ensure we can access all attributes
            result_dict = {}
            
            # Try to convert the result to a dictionary
            try:
                # First try to convert directly
                result_dict = dict(result)
            except (TypeError, ValueError):
                # If that fails, try to extract attributes from the object
                try:
                    result_dict = result.__dict__
                except AttributeError:
                    # If that fails too, try to extract items one by one
                    for key in dir(result):
                        if not key.startswith('_') and not callable(getattr(result, key, None)):
                            try:
                                result_dict[key] = getattr(result, key)
                            except (AttributeError, TypeError):
                                pass
            
            # Extract data from the result dictionary
            context_items = result_dict.get('context_items', [])
            sources = result_dict.get('sources', [])
            citations = result_dict.get('citations', {})
            final_context = result_dict.get('final_context', '')
            
            # If we couldn't extract the data from the result dictionary, try to access it directly
            if not context_items and hasattr(result, 'context_items'):
                context_items = result.context_items
                
            if not sources and hasattr(result, 'sources'):
                sources = result.sources
                
            if not citations and hasattr(result, 'citations'):
                citations = result.citations
                
            if not final_context and hasattr(result, 'final_context'):
                final_context = result.final_context
            
            # Extract the final context, ensuring it's not empty
            if not final_context and context_items:
                # If no final_context but we have context_items, join them
                final_context = "\n\n".join(context_items)
                print_agent_output("Using joined context_items as final context", "MASTER")
            elif not final_context:
                # Create a default context if all else fails
                final_context = f"Research on: {self.task.get('query', '')}\n\nNo specific research data was collected."
                print_agent_output("Using default context as final context", "MASTER")
            
            # If we have sources but they're not in the right format, try to fix them
            processed_sources = []
            for source in sources:
                if isinstance(source, dict):
                    processed_sources.append(source)
                elif isinstance(source, str):
                    # Try to parse the source string
                    if source.startswith('http'):
                        processed_sources.append({
                            'title': 'Source from URL',
                            'url': source,
                            'content': ''
                        })
                    else:
                        processed_sources.append({
                            'title': 'Source',
                            'url': '',
                            'content': source
                        })
            
            # If we still don't have any sources but we have context, create a source from the context
            if not processed_sources and final_context:
                processed_sources.append({
                    'title': f"Research on {self.task.get('query', '')}",
                    'url': '',
                    'content': final_context
                })
            
            # Log the final result
            print_agent_output(
                f"Final result: {len(final_context)} chars context, {len(processed_sources)} sources, {len(citations)} citations",
                "MASTER"
            )
            
            # Return the result
            return {
                "query": self.task.get("query", ""),
                "context": final_context,
                "sources": processed_sources,
                "citations": citations
            }
            
        except Exception as e:
            # Log the error
            print_agent_output(f"Error running research workflow: {str(e)}", "MASTER")
            
            # Return a default result
            return {
                "query": self.task.get("query", ""),
                "context": f"Research on: {self.task.get('query', '')}\n\nAn error occurred during research: {str(e)}",
                "sources": [],
                "citations": {}
            } 