from typing import Dict, List, Any
from datetime import datetime
from ...agents.utils.llms import call_model
from .base import DeepResearchAgent

class DeepExplorerAgent(DeepResearchAgent):
    """Agent responsible for exploring research queries and generating search queries"""
    
    async def generate_search_queries(self, query: str, num_queries: int = 3) -> List[Dict[str, str]]:
        """Generate SERP queries for research"""
        await self._stream_or_print(f"Generating {num_queries} search queries for: {query}", "EXPLORER")
        
        # Get current time for context
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        prompt = [
            {"role": "system", "content": "You are an expert researcher generating search queries."},
            {"role": "user",
             "content": f"""Given the following prompt, generate {num_queries} unique search queries to research the topic thoroughly. For each query, provide a research goal.

Current time: {current_time}

Consider the current time when generating queries, especially for time-sensitive topics. Include recent developments up to {current_time} when relevant.

Format as 'Query: <query>' followed by 'Goal: <goal>' for each pair.

Research topic: {query}"""}
        ]

        response = await call_model(
            prompt=prompt,
            model="gpt-4o",
            temperature=0.4
        )

        lines = response.split('\n')
        queries = []
        current_query = {}

        for line in lines:
            line = line.strip()
            if line.startswith('Query:'):
                if current_query:
                    queries.append(current_query)
                current_query = {'query': line.replace('Query:', '').strip()}
            elif line.startswith('Goal:') and current_query:
                current_query['researchGoal'] = line.replace('Goal:', '').strip()

        if current_query:
            queries.append(current_query)

        await self._stream_or_print(f"Generated {len(queries)} search queries", "EXPLORER")
        return queries[:num_queries]
        
    async def generate_research_plan(self, query: str, num_questions: int = 3) -> List[str]:
        """Generate follow-up questions to clarify research direction"""
        await self._stream_or_print(f"Generating research plan for: {query}", "EXPLORER")
        
        # Get current time for context
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        prompt = [
            {"role": "system", "content": "You are an expert researcher. Your task is to analyze the original query and generate targeted questions that explore different aspects and time periods of the topic."},
            {"role": "user",
             "content": f"""Original query: {query}

Current time: {current_time}

Based on the query and the current time, generate {num_questions} unique questions. Each question should explore a different aspect or time period of the topic, considering recent developments up to {current_time}.

Format each question on a new line starting with 'Question: '"""}
        ]

        response = await call_model(
            prompt=prompt,
            model="gpt-4o",
            temperature=0.4
        )

        questions = [q.replace('Question:', '').strip()
                     for q in response.split('\n')
                     if q.strip().startswith('Question:')]
                     
        await self._stream_or_print(f"Generated {len(questions)} research questions", "EXPLORER")
        return questions[:num_questions] 