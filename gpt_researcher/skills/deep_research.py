from typing import List, Dict, Any, Optional, Set
import asyncio
import logging
import time
from datetime import datetime, timedelta
from ..utils.llm import create_chat_completion
from ..utils.enum import ReportType, ReportSource, Tone

logger = logging.getLogger(__name__)


class ResearchProgress:
    def __init__(self, total_depth: int, total_breadth: int):
        self.current_depth = 1  # Start from 1 and increment up to total_depth
        self.total_depth = total_depth
        self.current_breadth = 0  # Start from 0 and count up to total_breadth as queries complete
        self.total_breadth = total_breadth
        self.current_query: Optional[str] = None
        self.total_queries = 0
        self.completed_queries = 0


class DeepResearchSkill:
    def __init__(self, agent):
        self.agent = agent
        self.breadth = getattr(agent.cfg, 'deep_research_breadth', 4)
        self.depth = getattr(agent.cfg, 'deep_research_depth', 2)
        self.concurrency_limit = getattr(agent.cfg, 'deep_research_concurrency', 2)
        self.websocket = agent.websocket
        self.tone = agent.tone
        self.config_path = agent.cfg.config_path if hasattr(agent.cfg, 'config_path') else None
        self.headers = agent.headers or {}
        self.visited_urls = agent.visited_urls
        self.learnings = []
        self.research_sources = []  # Track all research sources
        self.context = []  # Track all context

    async def generate_feedback(self, query: str, num_questions: int = 3) -> List[str]:
        """Generate follow-up questions to clarify research direction"""
        messages = [
            {"role": "system", "content": "You are an expert researcher helping to clarify research directions."},
            {"role": "user",
             "content": f"Given the following query from the user, ask some follow up questions to clarify the research direction. Return a maximum of {num_questions} questions, but feel free to return less if the original query is clear. Format each question on a new line starting with 'Question: ': {query}"}
        ]

        response = await create_chat_completion(
            messages=messages,
            llm_provider=self.agent.cfg.smart_llm_provider,
            model=self.agent.cfg.smart_llm_model,
            temperature=0.4,
            max_tokens=1000
        )

        questions = [q.replace('Question:', '').strip()
                     for q in response.split('\n')
                     if q.strip().startswith('Question:')]
        return questions[:num_questions]

    async def generate_serp_queries(self, query: str, num_queries: int = 3) -> List[Dict[str, str]]:
        """Generate SERP queries for research"""
        messages = [
            {"role": "system", "content": "You are an expert researcher generating search queries."},
            {"role": "user",
             "content": f"Given the following prompt, generate {num_queries} unique search queries to research the topic thoroughly. For each query, provide a research goal. Format as 'Query: <query>' followed by 'Goal: <goal>' for each pair: {query}"}
        ]

        response = await create_chat_completion(
            messages=messages,
            llm_provider=self.agent.cfg.strategic_llm_provider,
            model=self.agent.cfg.strategic_llm_model,
            reasoning_effort="medium",
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

        return queries[:num_queries]

    async def process_serp_result(self, query: str, context: str, num_learnings: int = 3) -> Dict[str, List[str]]:
        """Process research results to extract learnings and follow-up questions"""
        messages = [
            {"role": "system", "content": "You are an expert researcher analyzing search results."},
            {"role": "user",
             "content": f"Given the following research results for the query '{query}', extract key learnings and suggest follow-up questions. For each learning, include a citation to the source URL if available. Format each learning as 'Learning [source_url]: <insight>' and each question as 'Question: <question>':\n\n{context}"}
        ]

        response = await create_chat_completion(
            messages=messages,
            llm_provider=self.agent.cfg.strategic_llm_provider,
            model=self.agent.cfg.strategic_llm_model,
            temperature=0.4,
            reasoning_effort="high",
            max_tokens=1000
        )

        lines = response.split('\n')
        learnings = []
        questions = []
        citations = {}

        for line in lines:
            line = line.strip()
            if line.startswith('Learning'):
                import re
                url_match = re.search(r'\[(.*?)\]:', line)
                if url_match:
                    url = url_match.group(1)
                    learning = line.split(':', 1)[1].strip()
                    learnings.append(learning)
                    citations[learning] = url
                else:
                    # Try to find URL in the line itself
                    url_match = re.search(
                        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', line)
                    if url_match:
                        url = url_match.group(0)
                        learning = line.replace(url, '').replace('Learning:', '').strip()
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
            on_progress=None
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
        all_context = []
        all_sources = []

        # Process queries with concurrency limit
        semaphore = asyncio.Semaphore(self.concurrency_limit)

        async def process_query(serp_query: Dict[str, str]) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    progress.current_query = serp_query['query']
                    if on_progress:
                        on_progress(progress)

                    from .. import GPTResearcher
                    researcher = GPTResearcher(
                        query=serp_query['query'],
                        report_type=ReportType.ResearchReport.value,
                        report_source=ReportSource.Web.value,
                        tone=self.tone,
                        websocket=self.websocket,
                        config_path=self.config_path,
                        headers=self.headers,
                        visited_urls=self.visited_urls
                    )

                    # Conduct research
                    context = await researcher.conduct_research()

                    # Get results and visited URLs
                    visited = researcher.visited_urls
                    sources = researcher.research_sources

                    # Process results to extract learnings and citations
                    results = await self.process_serp_result(
                        query=serp_query['query'],
                        context=context
                    )

                    # Update progress
                    progress.completed_queries += 1
                    progress.current_breadth += 1  # Increment breadth as queries complete
                    if on_progress:
                        on_progress(progress)

                    return {
                        'learnings': results['learnings'],
                        'visited_urls': list(visited),
                        'followUpQuestions': results['followUpQuestions'],
                        'researchGoal': serp_query['researchGoal'],
                        'citations': results['citations'],
                        'context': context if context else "",
                        'sources': sources if sources else []
                    }

                except Exception as e:
                    logger.error(f"Error processing query '{serp_query['query']}': {str(e)}")
                    return None

        # Process queries concurrently with limit
        tasks = [process_query(query) for query in serp_queries]
        results = await asyncio.gather(*tasks)
        results = [r for r in results if r is not None]  # Filter out failed queries

        # Update breadth progress based on successful queries
        progress.current_breadth = len(results)
        if on_progress:
            on_progress(progress)

        # Collect all results
        for result in results:
            all_learnings.extend(result['learnings'])
            all_visited_urls.update(result['visited_urls'])
            all_citations.update(result['citations'])
            if result['context']:
                all_context.append(result['context'])
            if result['sources']:
                all_sources.extend(result['sources'])

            # Continue deeper if needed
            if depth > 1:
                new_breadth = max(2, breadth // 2)
                new_depth = depth - 1
                progress.current_depth += 1  # Increment depth as we go deeper

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
                all_visited_urls.update(deeper_results['visited_urls'])
                all_citations.update(deeper_results['citations'])
                if deeper_results.get('context'):
                    all_context.extend(deeper_results['context'])
                if deeper_results.get('sources'):
                    all_sources.extend(deeper_results['sources'])

        # Update class tracking
        self.context.extend(all_context)
        self.research_sources.extend(all_sources)

        return {
            'learnings': list(set(all_learnings)),
            'visited_urls': list(all_visited_urls),
            'citations': all_citations,
            'context': all_context,
            'sources': all_sources
        }

    def _build_research_query(self, initial_query: str, follow_up_questions: List[str]) -> str:
        """Build the research query combining initial query and follow-up questions if they exist.

        Args:
            initial_query: The initial query from the user
            follow_up_questions: List of follow-up questions, can be empty

        Returns:
            str: Formatted query string combining initial query and follow-up Q&A if they exist

        Example:
            >>> _build_research_query("What is Python?", ["How is it used?"])
            "Initial Query: What is Python?
            Follow-up Questions and Answers:
            Q: How is it used?
            A: Automatically proceeding with research"
        """
        if not initial_query:
            raise ValueError("Initial query cannot be empty")

        # Define templates as constants for better maintainability
        BASE_TEMPLATE = "Initial Query: {query}"
        FOLLOWUP_TEMPLATE = "\nFollow-up Questions and Answers:\n{qa_section}"
        DEFAULT_ANSWER = "Automatically proceeding with research"

        # Handle base case
        if not follow_up_questions:
            return BASE_TEMPLATE.format(query=initial_query.strip())

        # Build Q&A pairs
        qa_pairs: List[str] = [
            f"Q: {question.strip()}\nA: {DEFAULT_ANSWER}"
            for question in follow_up_questions
            if question.strip()  # Skip empty questions
        ]

        # Only add follow-up section if we have valid questions
        if qa_pairs:
            return BASE_TEMPLATE.format(query=initial_query.strip()) + \
                FOLLOWUP_TEMPLATE.format(qa_section='\n'.join(qa_pairs))

        return BASE_TEMPLATE.format(query=initial_query.strip())

    async def run(self, on_progress=None) -> str:
        """Run the deep research process and generate final report.

        Args:
            on_progress: Optional callback function to report research progress

        Returns:
            str: The research context with citations

        Raises:
            ValueError: If the agent query is empty
        """
        if not self.agent.query:
            raise ValueError("Research query cannot be empty")

        start_time = time.time()

        try:
            follow_up_questions = await self.generate_feedback(self.agent.query)
            combined_query = self._build_research_query(self.agent.query, follow_up_questions)

            results = await self.deep_research(
                query=combined_query,
                breadth=self.breadth,
                depth=self.depth,
                on_progress=on_progress
            )

            # Prepare context with citations
            context_with_citations = []
            for learning in results['learnings']:
                citation = results['citations'].get(learning, '')
                if citation:
                    context_with_citations.append(f"{learning} [Source: {citation}]")
                else:
                    context_with_citations.append(learning)

            # Add all research context
            if results.get('context'):
                context_with_citations.extend(results['context'])

            # Update agent state
            self.agent.context = "\n".join(context_with_citations)
            self.agent.visited_urls = results['visited_urls']
            if results.get('sources'):
                self.agent.research_sources = results['sources']

            # Log execution time
            execution_time = timedelta(seconds=time.time() - start_time)
            logger.info(f"Total research execution time: {execution_time}")

            return self.agent.context

        except Exception as e:
            logger.error(f"Error during research process: {str(e)}")
            raise