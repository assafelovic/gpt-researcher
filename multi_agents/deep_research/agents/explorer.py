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
        
    async def generate_research_plan(self, query: str, query_titles: List[str] = None, num_questions: int = 3) -> List[str]:
        """Generate a research plan based on query titles"""
        await self._stream_or_print(f"Generating research plan for: {query}", "EXPLORER")
        
        # Get current time for context
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Use query titles if provided, otherwise just use the main query
        query_context = ""
        if query_titles and isinstance(query_titles, list):
            query_context = "\n".join([f"- {title}" for title in query_titles])
        
        prompt = [
            {"role": "system", "content": "You are an expert researcher. Your task is to analyze the original query and sub-queries to generate a comprehensive research plan."},
            {"role": "user",
             "content": f"""Original query: {query}

Current time: {current_time}

Sub-queries:
{query_context}

Based on the original query and sub-queries, generate {num_questions} research questions that will guide our investigation. Each question should explore a different aspect of the topic, considering recent developments up to {current_time}.

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

    async def generate_follow_up_questions(self, query: str, context: str, num_questions: int = 3) -> List[str]:
        """Generate follow-up questions based on research context"""
        await self._stream_or_print(f"Generating follow-up questions for: {query}", "EXPLORER")
        
        prompt = [
            {"role": "system", "content": "You are an expert researcher identifying follow-up questions."},
            {"role": "user",
             "content": f"""Based on the following research context for the query '{query}', generate {num_questions} follow-up questions that would deepen the research. These questions should explore aspects not fully covered in the current research.

Research context:
{context}

IMPORTANT: Format each question on a new line starting with 'Question: ' - this exact format is required."""}
        ]

        response = await call_model(
            prompt=prompt,
            model="gpt-4o",
            temperature=0.4
        )

        # First try to extract questions with the 'Question:' prefix
        questions = [q.replace('Question:', '').strip()
                     for q in response.split('\n')
                     if q.strip().startswith('Question:')]
        
        # If no questions were found with the prefix, try to extract questions by line
        if not questions:
            # Split by newlines and filter out empty lines
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            
            # If we have at least num_questions lines, assume they are the questions
            if len(lines) >= num_questions:
                questions = lines[:num_questions]
            # If we have fewer lines but at least one, use what we have
            elif lines:
                questions = lines
        
        await self._stream_or_print(f"Generated {len(questions)} follow-up questions", "EXPLORER")
        return questions[:num_questions] 