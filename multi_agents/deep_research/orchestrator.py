import os
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta

# Basic LangGraph imports that should be available in all versions
try:
    from langgraph.graph import StateGraph, START, END
except ImportError:
    logging.error("Could not import StateGraph from langgraph.graph. Please check your LangGraph installation.")
    raise

# Try to import MemorySaver from different possible locations
try:
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    try:
        from langgraph.checkpoint import MemorySaver
    except ImportError:
        # Create a simple in-memory checkpointer if not available
        class MemorySaver:
            def __init__(self):
                self.memory = {}
                
            def get(self, key, default=None):
                return self.memory.get(key, default)
                
            def put(self, key, value):
                self.memory[key] = value
                return key
        logging.warning("Using a simplified MemorySaver implementation as the original could not be imported.")

# Try to import Command and interrupt, create placeholders if not available
try:
    from langgraph.types import Command, interrupt
except ImportError:
    try:
        from langgraph.graph.types import Command, interrupt
    except ImportError:
        # Create placeholder implementations
        class Command:
            def __init__(self, resume=None, update=None):
                self.resume = resume
                self.update = update
        
        def interrupt(data):
            """Placeholder for interrupt function if not available."""
            logging.warning("Interrupt functionality not available in this version of LangGraph.")
            return {"action": "Continue"}
        logging.warning("Using placeholder implementations for Command and interrupt.")

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
    
    def __init__(self, task: dict, websocket=None, stream_output=None, tone=None, headers=None, human_review_enabled=False):
        self.task = task
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}
        self.tone = tone
        self.task_id = self._generate_task_id()
        self.output_dir = self._create_output_directory()
        self.human_review_enabled = human_review_enabled
        
        # Research parameters
        self.breadth = task.get('deep_research_breadth', 4)
        self.depth = task.get('deep_research_depth', 2)
        self.concurrency_limit = task.get('deep_research_concurrency', 2)
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Initialize checkpointer
        self.checkpointer = MemorySaver()
        
    async def _stream_or_print(self, message: str, agent_type: str = "MASTER"):
        """
        Stream a message to the websocket or print it to the console.
        
        Args:
            message: The message to stream or print
            agent_type: The type of agent sending the message (for coloring)
        """
        if self.websocket and self.stream_output:
            # Stream to websocket if available
            await self.stream_output(
                "logs",
                agent_type.lower(),
                message,
                self.websocket
            )
        else:
            # Otherwise print to console
            print_agent_output(message, agent_type)
            
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
        
        # Update the state's total_breadth directly
        state.total_breadth = total_breadth
        
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
        
        # Update the state's current_breadth
        state.current_breadth = query_index + 1
        
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
            
        # Reset current_breadth to 0 at the start
        state.current_breadth = 0
        
        async def process_with_semaphore(index):
            """Process a query with semaphore for concurrency control"""
            async with semaphore:
                try:
                    result = await self.process_query(state, index)
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
        
        # Update the state's current_breadth to the total after all queries are processed
        state.current_breadth = len(state.search_queries)
        
        # Combine results
        combined_context_items = list(state.context_items)  # Create a copy to avoid modifying the original
        combined_sources = list(state.sources)  # Create a copy
        combined_citations = dict(state.citations)  # Create a copy
        
        # Track how many results actually contributed data
        results_with_context = 0
        results_with_sources = 0
        
        for i, result in enumerate(results):
            # Add context item
            context_item = result.get("context_item", "")
            if context_item:
                combined_context_items.append(context_item)
                results_with_context += 1
                
            # Add sources
            sources = result.get("sources", [])
            if sources:
                combined_sources.extend(sources)
                results_with_sources += 1
                
            # Add citations
            citations = result.get("citations", {})
            if citations:
                combined_citations.update(citations)
        
        # Debug log how many results contributed data
        print_agent_output(
            f"{results_with_context}/{len(results)} results contributed context items, {results_with_sources}/{len(results)} contributed sources",
            "MASTER"
        )
        
        # Return combined results following LangGraph pattern
        return {
            "context_items": combined_context_items,
            "sources": combined_sources,
            "citations": combined_citations,
            "current_depth": state.current_depth  # Explicitly include current_depth
        }
        
    async def review_research(self, state: DeepResearchState) -> dict:
        """Review the research results"""
        # Get the reviewer agent
        reviewer = self.agents.get("reviewer")
        
        # Update progress
        await self._on_progress(state, current_depth=state.current_depth)
        
        # Log the review process
        await self._stream_or_print(f"Reviewing research results for depth {state.current_depth}...", "REVIEWER")
        
        # If human review is enabled, request human input
        if self.human_review_enabled:
            return await self.human_review_research(state)
        
        # Otherwise, use the AI reviewer
        review_result = await reviewer.review(
            state.query,
            state.context_items,
            state.current_depth,
            state.total_depth
        )
        
        # Set the review in the state
        state.set_review(review_result)
        
        # Set follow-up questions if available
        if "follow_up_questions" in review_result:
            state.set_follow_up_questions(review_result["follow_up_questions"])
            
        return state
        
    async def human_review_research(self, state: DeepResearchState) -> dict:
        """Request human review of research results"""
        # Prepare a summary of the research for human review
        context_summary = "\n\n".join(state.context_items[:3])  # Show first 3 items
        if len(state.context_items) > 3:
            context_summary += f"\n\n... and {len(state.context_items) - 3} more items"
            
        sources_summary = "\n".join([
            f"- {s.get('title', 'Source')} ({s.get('url', 'No URL')})"
            for s in state.sources[:5]  # Show first 5 sources
        ])
        if len(state.sources) > 5:
            sources_summary += f"\n... and {len(state.sources) - 5} more sources"
            
        # Create a summary message
        summary = f"""
Research Progress: Depth {state.current_depth} of {state.total_depth}

Query: {state.query}

Context Items: {len(state.context_items)}
{context_summary}

Sources: {len(state.sources)}
{sources_summary}

Learnings: {len(state.learnings)}
"""
        
        # Log that we're waiting for human review
        await self._stream_or_print("Waiting for human review...", "HUMAN")
        
        # Use interrupt to pause execution and wait for human input
        try:
            human_response = interrupt({
                "summary": summary,
                "question": "Would you like to continue with this research or provide feedback?",
                "options": ["Continue", "Add feedback", "Stop research"]
            })
            
            # Process the human response
            if human_response.get("action") == "Stop research":
                # If the human wants to stop, set current_depth to total_depth to end recursion
                state.current_depth = state.total_depth
                state.set_review({"follow_up_questions": []})
                await self._stream_or_print("Research stopped by human reviewer", "HUMAN")
                
            elif human_response.get("action") == "Add feedback":
                # Add the human feedback as a context item
                feedback = human_response.get("feedback", "")
                if feedback:
                    state.add_context_item(f"Human feedback: {feedback}")
                    await self._stream_or_print(f"Added human feedback: {feedback}", "HUMAN")
                    
                # Set any follow-up questions provided by the human
                follow_ups = human_response.get("follow_up_questions", [])
                if follow_ups:
                    state.set_follow_up_questions(follow_ups)
                    await self._stream_or_print(f"Added {len(follow_ups)} follow-up questions from human", "HUMAN")
                    
                state.set_review({"follow_up_questions": follow_ups})
                
            else:
                # Continue with default AI-generated follow-up questions
                reviewer = self.agents.get("reviewer")
                review_result = await reviewer.review(
                    state.query,
                    state.context_items,
                    state.current_depth,
                    state.total_depth
                )
                state.set_review(review_result)
                
                # Set follow-up questions if available
                if "follow_up_questions" in review_result:
                    state.set_follow_up_questions(review_result["follow_up_questions"])
                
        except Exception as e:
            logger.warning(f"Human review interrupted with error: {str(e)}. Falling back to AI reviewer.")
                
        return state
        
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
        
        # First, call the state's finalize_context method to ensure it's set
        final_context = state.finalize_context()
        
        # Create a temporary state for the finalizer
        finalizer_state = {
            "query": state.query,
            "context_items": state.context_items,
            "sources": state.sources,
            "citations": state.citations,
            "final_context": final_context  # Include the finalized context
        }
        
        # Run the finalizer to generate the final context
        finalizer_result = await finalizer.run(finalizer_state)
        
        # Ensure final_context is set
        if not finalizer_result.get("final_context") and final_context:
            finalizer_result["final_context"] = final_context
        
        # Return the finalized research state
        return {
            "context": finalizer_result.get("context", ""),
            "summary": finalizer_result.get("summary", ""),
            "sources": finalizer_result.get("sources", []),
            "citations": finalizer_result.get("citations", {}),
            "final_context": finalizer_result.get("final_context", final_context),  # Use the state's final_context as fallback
            "learnings": finalizer_result.get("learnings", [])
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
        
        # Add edges with START and END nodes
        workflow.add_edge(START, "generate_queries")
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
        
        return workflow
        
    async def run(self) -> Dict[str, Any]:
        """Run the deep research process"""
        # Log the start of the research process
        await self._log_research_start()
        
        # Create the workflow
        workflow = self.create_workflow()
        
        # Compile the workflow with checkpointer
        chain = workflow.compile(checkpointer=self.checkpointer)
        
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
                "thread_id": str(self.task_id),  # Convert to string for compatibility
                "checkpoint_ns": "",  # Use default namespace
            }
        }
        
        try:
            # Use ainvoke to run the workflow asynchronously
            print_agent_output("Starting LangGraph workflow...", "MASTER")
            result = await chain.ainvoke(initial_state, config=config)
            print_agent_output("LangGraph workflow completed", "MASTER")

            final_context = result.get('final_context', '')
            sources = result.get('sources', [])
            citations = result.get('citations', {})
            learnings = result.get('learnings', [])
            
            # If final_context is empty but we have context_items, join them
            if not final_context:
                context_items = result.get('context_items', []) if hasattr(result, 'get') else getattr(result, 'context_items', [])
                if context_items:
                    print_agent_output(f"No final_context found, creating from {len(context_items)} context items", "MASTER")
                    final_context = "\n\n".join(context_items)
                else:
                    print_agent_output("No final_context or context_items found", "MASTER")
                    # Try to get context from the state directly
                    try:
                        state = chain.get_state(config)
                        if state and hasattr(state, 'values'):
                            state_obj = state.values
                            if hasattr(state_obj, 'finalize_context'):
                                print_agent_output("Calling finalize_context on state", "MASTER")
                                final_context = state_obj.finalize_context()
                            elif hasattr(state_obj, 'context_items'):
                                context_items = getattr(state_obj, 'context_items', [])
                                if context_items:
                                    print_agent_output(f"Creating final_context from state's {len(context_items)} context items", "MASTER")
                                    final_context = "\n\n".join(context_items)
                    except Exception as e:
                        print_agent_output(f"Error getting state: {str(e)}", "MASTER")
            
            # Log the final result
            print_agent_output(
                f"Final result: {len(final_context)} chars context, {len(sources)} sources, {len(citations)} citations",
                "MASTER"
            )
            
            # Return the result
            return {
                "query": self.task.get("query", ""),
                "context": final_context,
                "sources": sources,
                "citations": citations,
                "execution_time": str(datetime.now() - datetime.fromtimestamp(self.task_id)),
                "learnings": learnings
            }
            
        except Exception as e:
            # Log the error
            print_agent_output(f"Error running research workflow: {str(e)}", "MASTER")
            logger.exception("Error in research workflow")
            
            # Return a default result
            return {
                "query": self.task.get("query", ""),
                "context": f"Research on: {self.task.get('query', '')}\n\nAn error occurred during research: {str(e)}",
                "sources": [],
                "citations": {},
                "execution_time": str(datetime.now() - datetime.fromtimestamp(self.task_id)),
                "learnings": []
            }