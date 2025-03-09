"""
Planner Agent for Deep Research

This agent is responsible for generating research plans and search queries.
"""

from typing import Dict, Any, List
import asyncio

from ...agents.utils.views import print_agent_output
from .base import DeepResearchAgent

class PlannerAgent(DeepResearchAgent):
    """
    Agent responsible for planning the research process, including generating search queries
    and creating a research plan.
    """
    
    def __init__(self, websocket=None, stream_output=None, tone=None, headers=None):
        """
        Initialize the agent.
        
        Args:
            websocket: Optional websocket for streaming output
            stream_output: Optional stream output function
            tone: Optional tone for the research
            headers: Optional headers for API requests
        """
        super().__init__(websocket, stream_output, tone, headers)
    
    async def generate_search_queries(self, query: str, num_queries: int = 4) -> List[Dict[str, str]]:
        """
        Generate search queries for research.
        
        Args:
            query: The main research query
            num_queries: Number of search queries to generate
            
        Returns:
            List of search query objects with title and query
        """
        # Log the action
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "generating_search_queries",
                f"Generating {num_queries} search queries for '{query}'...",
                self.websocket,
            )
        else:
            print_agent_output(
                f"Generating {num_queries} search queries for '{query}'...",
                agent="PLANNER",
            )
        
        # Use the explorer agent to generate search queries
        # This is a simplified version that would be implemented with LLM calls
        # For now, we'll use a basic approach to generate queries
        
        # Get model from config
        from gpt_researcher.config.config import Config
        cfg = Config()
        model = cfg.smart_llm_model
        
        # Create the prompt for generating search queries
        from ...agents.utils.llms import call_model
        prompt = [
            {
                "role": "system",
                "content": f"You are a research planner. Your task is to generate {num_queries} specific search queries to thoroughly research a topic."
            },
            {
                "role": "user",
                "content": f"""I need to research the following topic:
                
Topic: {query}

Please generate {num_queries} specific search queries that would help me thoroughly research this topic.
Each query should focus on a different aspect of the topic to ensure comprehensive coverage.

Return your response as a JSON array of objects, each with 'title' and 'query' fields.
For example:
[
  {{
    "title": "Brief descriptive title for query 1",
    "query": "Specific search query 1"
  }},
  {{
    "title": "Brief descriptive title for query 2",
    "query": "Specific search query 2"
  }}
]

Make sure each query is specific enough to return relevant results but broad enough to capture important information.
"""
            }
        ]
        
        # Call the model to generate search queries
        response = await call_model(
            prompt,
            model,
            response_format="json",
        )
        
        # Handle potential errors
        if not response or not isinstance(response, list):
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "error",
                    "Error generating search queries. Using default queries.",
                    self.websocket,
                )
            else:
                print_agent_output(
                    "Error generating search queries. Using default queries.",
                    agent="PLANNER",
                )
            # Create default queries
            return [{"title": f"Query {i+1}", "query": f"{query} aspect {i+1}"} for i in range(num_queries)]
        
        return response
    
    async def generate_research_plan(self, query: str, search_queries: List[Dict[str, str]]) -> str:
        """
        Generate a research plan based on search queries.
        
        Args:
            query: The main research query
            search_queries: List of search query objects
            
        Returns:
            Research plan as a string
        """
        # Log the action
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "generating_research_plan",
                f"Generating research plan for '{query}' with {len(search_queries)} queries...",
                self.websocket,
            )
        else:
            print_agent_output(
                f"Generating research plan for '{query}' with {len(search_queries)} queries...",
                agent="PLANNER",
            )
        
        # Extract query titles for planning
        query_titles = [q.get("title", f"Query {i+1}") for i, q in enumerate(search_queries)]
        
        # Get model from config
        from gpt_researcher.config.config import Config
        cfg = Config()
        model = cfg.smart_llm_model
        
        # Create the prompt for generating the research plan
        from ...agents.utils.llms import call_model
        prompt = [
            {
                "role": "system",
                "content": "You are a research planner. Your task is to create a structured research plan based on a set of search queries."
            },
            {
                "role": "user",
                "content": f"""I need to research the following topic:
                
Topic: {query}

I have the following search queries to explore:
{', '.join(query_titles)}

Please create a structured research plan that outlines how to approach this research topic using these queries.
The plan should include:
1. The overall research goal
2. How each query contributes to understanding the topic
3. What specific information to look for in each query
4. How to synthesize the findings into a comprehensive understanding

Your plan should be detailed but concise, focusing on the strategy rather than the actual research content.
"""
            }
        ]
        
        # Call the model to generate the research plan
        plan = await call_model(
            prompt,
            model,
        )
        
        # Handle potential errors
        if not plan or not isinstance(plan, str):
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "error",
                    "Error generating research plan. Using default plan.",
                    self.websocket,
                )
            else:
                print_agent_output(
                    "Error generating research plan. Using default plan.",
                    agent="PLANNER",
                )
            # Create default plan
            return f"Research Plan for '{query}':\n\n" + "\n".join([f"- Explore {title}" for title in query_titles])
        
        return plan
    
    async def run(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the planner agent.
        
        Args:
            research_state: Current research state
            
        Returns:
            Updated research state with search queries and research plan
        """
        query = research_state.get("query", "")
        breadth = research_state.get("breadth", 4)
        
        # Generate search queries
        search_queries = await self.generate_search_queries(query, num_queries=breadth)
        
        # Generate research plan
        research_plan_str = await self.generate_research_plan(query, search_queries)
        
        # Convert research plan string to list (split by newlines)
        research_plan = research_plan_str.split('\n')
        
        # Return updated research state
        return {
            **research_state,
            "search_queries": search_queries,
            "total_breadth": len(search_queries),
            "research_plan": research_plan
        } 