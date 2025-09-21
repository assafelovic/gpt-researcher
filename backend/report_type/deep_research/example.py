from typing import List, Dict, Any, Optional, Set
from fastapi import WebSocket
import asyncio
import logging
from gpt_researcher import GPTResearcher
from gpt_researcher.llm_provider.generic.base import ReasoningEfforts
from gpt_researcher.utils.llm import create_chat_completion
from gpt_researcher.utils.enum import ReportType, ReportSource, Tone

logger = logging.getLogger(__name__)

# Constants for models
GPT4_MODEL = "gpt-4o"  # For standard tasks
O3_MINI_MODEL = "o3-mini"  # For reasoning tasks
LLM_PROVIDER = "openai"

class ResearchProgress:
    def __init__(self, total_depth: int, total_breadth: int):
        self.current_depth = total_depth
        self.total_depth = total_depth
        self.current_breadth = total_breadth
        self.total_breadth = total_breadth
        self.current_query: Optional[str] = None
        self.total_queries = 0
        self.completed_queries = 0

class DeepResearch:
    def __init__(
        self,
        query: str,
        breadth: int = 4,
        depth: int = 2,
        websocket: Optional[WebSocket] = None,
        tone: Tone = Tone.Objective,
        config_path: Optional[str] = None,
        headers: Optional[Dict] = None,
        concurrency_limit: int = 2  # Match TypeScript version
    ):
        self.query = query
        self.breadth = breadth
        self.depth = depth
        self.websocket = websocket
        self.tone = tone
        self.config_path = config_path
        self.headers = headers or {}
        self.visited_urls: Set[str] = set()
        self.learnings: List[str] = []
        self.concurrency_limit = concurrency_limit

    async def generate_feedback(self, query: str, num_questions: int = 3) -> List[str]:
        """Generate follow-up questions to clarify research direction"""
        messages = [
            {"role": "system", "content": "You are an expert researcher helping to clarify research directions."},
            {"role": "user", "content": f"Given the following query from the user, ask some follow up questions to clarify the research direction. Return a maximum of {num_questions} questions, but feel free to return less if the original query is clear. Format each question on a new line starting with 'Question: ': {query}"}
        ]

        response = await create_chat_completion(
            messages=messages,
            llm_provider=LLM_PROVIDER,
            model=O3_MINI_MODEL,  # Using reasoning model for better question generation
            temperature=0.7,
            max_tokens=500,
            reasoning_effort=ReasoningEfforts.High.value
        )

        # Parse questions from response
        questions = [q.replace('Question:', '').strip()
                    for q in response.split('\n')
                    if q.strip().startswith('Question:')]
        return questions[:num_questions]

    async def generate_serp_queries(self, query: str, num_queries: int = 3) -> List[Dict[str, str]]:
        """Generate SERP queries for research"""
        messages = [
            {"role": "system", "content": "You are an expert researcher generating search queries."},
            {"role": "user", "content": f"Given the following prompt, generate {num_queries} unique search queries to research the topic thoroughly. For each query, provide a research goal. Format as 'Query: <query>' followed by 'Goal: <goal>' for each pair: {query}"}
        ]

        response = await create_chat_completion(
            messages=messages,
            llm_provider=LLM_PROVIDER,
            model=GPT4_MODEL,  # Using GPT-4 for general task
            temperature=0.7,
            max_tokens=1000
        )

        # Parse queries and goals from response
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

        return queries[:num_queries]

    async def process_serp_result(self, query: str, context: str, num_learnings: int = 3) -> Dict[str, List[str]]:
        """Process research results to extract learnings and follow-up questions"""
        messages = [
            {"role": "system", "content": "You are an expert researcher analyzing search results."},
            {"role": "user", "content": f"Given the following research results for the query '{query}', extract key learnings and suggest follow-up questions. For each learning, include a citation to the source URL if available. Format each learning as 'Learning [source_url]: <insight>' and each question as 'Question: <question>':\n\n{context}"}
        ]

        response = await create_chat_completion(
            messages=messages,
            llm_provider=LLM_PROVIDER,
            model=O3_MINI_MODEL,  # Using reasoning model for analysis
            temperature=0.7,
            max_tokens=1000,
            reasoning_effort=ReasoningEfforts.High.value
        )

        # Parse learnings and questions with citations
        lines = response.split('\n')
        learnings = []
        questions = []
        citations = {}

        for line in lines:
            line = line.strip()
            if line.startswith('Learning'):
                # Extract URL if present in square brackets
                import re
                url_match = re.search(r'\[(.*?)\]:', line)
                if url_match:
                    url = url_match.group(1)
                    learning = line.split(':', 1)[1].strip()
                    learnings.append(learning)
                    citations[learning] = url
                else:
                    learnings.append(line.replace('Learning:', '').strip())
            elif line.startswith('Question:'):
                questions.append(line.replace('Question:', '').strip())

        return {
            'learnings': learnings[:num_learnings],
            'followUpQuestions': questions[:num_learnings],
            'citations': citations
        }

    async def deep_research(
        self,
        query: str,
        breadth: int,
        depth: int,
        learnings: List[str] = None,
        citations: Dict[str, str] = None,
        visited_urls: Set[str] = None,
        on_progress = None
    ) -> Dict[str, Any]:
        """Conduct deep iterative research"""
        if learnings is None:
            learnings = []
        if citations is None:
            citations = {}
        if visited_urls is None:
            visited_urls = set()

        progress = ResearchProgress(depth, breadth)

        if on_progress:
            on_progress(progress)

        # Generate search queries
        serp_queries = await self.generate_serp_queries(query, num_queries=breadth)
        progress.total_queries = len(serp_queries)

        all_learnings = learnings.copy()
        all_citations = citations.copy()
        all_visited_urls = visited_urls.copy()

        # Process queries with concurrency limit
        semaphore = asyncio.Semaphore(self.concurrency_limit)

        async def process_query(serp_query: Dict[str, str]) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    progress.current_query = serp_query['query']
                    if on_progress:
                        on_progress(progress)

                    # Initialize researcher for this query
                    researcher = GPTResearcher(
                        query=serp_query['query'],
                        report_type=ReportType.ResearchReport.value,
                        report_source=ReportSource.Web.value,
                        tone=self.tone,
                        websocket=self.websocket,
                        config_path=self.config_path,
                        headers=self.headers
                    )

                    # Conduct research
                    await researcher.conduct_research()

                    # Get results
                    context = researcher.context
                    visited = set(researcher.visited_urls)

                    # Process results
                    results = await self.process_serp_result(
                        query=serp_query['query'],
                        context=context
                    )

                    # Update progress
                    progress.completed_queries += 1
                    if on_progress:
                        on_progress(progress)

                    return {
                        'learnings': results['learnings'],
                        'visited_urls': visited,
                        'followUpQuestions': results['followUpQuestions'],
                        'researchGoal': serp_query['researchGoal'],
                        'citations': results['citations']
                    }

                except Exception as e:
                    logger.error(f"Error processing query '{serp_query['query']}': {str(e)}")
                    return None

        # Process queries concurrently with limit
        tasks = [process_query(query) for query in serp_queries]
        results = await asyncio.gather(*tasks)
        results = [r for r in results if r is not None]  # Filter out failed queries

        # Collect all results
        for result in results:
            all_learnings.extend(result['learnings'])
            all_visited_urls.update(set(result['visited_urls']))
            all_citations.update(result['citations'])

            # Continue deeper if needed
            if depth > 1:
                new_breadth = max(2, breadth // 2)
                new_depth = depth - 1

                # Create next query from research goal and follow-up questions
                next_query = f"""
                Previous research goal: {result['researchGoal']}
                Follow-up questions: {' '.join(result['followUpQuestions'])}
                """

                # Recursive research
                deeper_results = await self.deep_research(
                    query=next_query,
                    breadth=new_breadth,
                    depth=new_depth,
                    learnings=all_learnings,
                    citations=all_citations,
                    visited_urls=all_visited_urls,
                    on_progress=on_progress
                )

                all_learnings = deeper_results['learnings']
                all_visited_urls = set(deeper_results['visited_urls'])
                all_citations.update(deeper_results['citations'])

        return {
            'learnings': list(set(all_learnings)),
            'visited_urls': list(all_visited_urls),
            'citations': all_citations
        }

    async def run(self, on_progress=None) -> str:
        """Run the deep research process and generate final report"""
        # Get initial feedback
        follow_up_questions = await self.generate_feedback(self.query)

        # Collect answers (this would normally come from user interaction)
        answers = ["Automatically proceeding with research"] * len(follow_up_questions)

        # Combine query and Q&A
        combined_query = f"""
        Initial Query: {self.query}
        Follow-up Questions and Answers:
        {' '.join([f'Q: {q}\nA: {a}' for q, a in zip(follow_up_questions, answers)])}
        """

        # Run deep research
        results = await self.deep_research(
            query=combined_query,
            breadth=self.breadth,
            depth=self.depth,
            on_progress=on_progress
        )

        # Generate final report
        researcher = GPTResearcher(
            query=self.query,
            report_type=ReportType.DetailedReport.value,
            report_source=ReportSource.Web.value,
            tone=self.tone,
            websocket=self.websocket,
            config_path=self.config_path,
            headers=self.headers
        )

        # Prepare context with citations
        context_with_citations = []
        for learning in results['learnings']:
            citation = results['citations'].get(learning, '')
            if citation:
                context_with_citations.append(f"{learning} [Source: {citation}]")
            else:
                context_with_citations.append(learning)

        # Set enhanced context for final report
        researcher.context = "\n".join(context_with_citations)
        researcher.visited_urls = set(results['visited_urls'])

        # Generate report
        report = await researcher.write_report()
        return report