from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from gpt_researcher.actions.query_processing import get_search_results
from gpt_researcher.llm_provider.generic.base import ReasoningEfforts
from gpt_researcher.utils.enum import ReportSource, ReportType, Tone
from gpt_researcher.utils.llm import create_chat_completion

if TYPE_CHECKING:
    import logging
    from pathlib import Path

    from backend.server.server_utils import CustomLogsHandler
    from fastapi import WebSocket

    from gpt_researcher.agent import GPTResearcher
    from gpt_researcher.utils.enum import Tone

logger: logging.Logger = logging.getLogger(__name__)

# Maximum words allowed in context (25k words for safety margin)
MAX_CONTEXT_WORDS = 25000


def count_words(text: str) -> int:
    """Count words in a text string."""
    return len(text.split())


def trim_context_to_word_limit(
    context_list: list[str],
    max_words: int = MAX_CONTEXT_WORDS,
) -> list[str]:
    """Trim context list to stay within word limit while preserving most recent/relevant items."""
    total_words: int = 0
    trimmed_context: list[str] = []

    # Process in reverse to keep most recent items
    for item in reversed(context_list):
        words: int = count_words(item)
        if total_words + words <= max_words:
            trimmed_context.insert(
                0, item
            )  # Insert at start to maintain original order
            total_words += words
        else:
            break

    return trimmed_context


class ResearchProgress:
    def __init__(
        self,
        total_depth: int,
        total_breadth: int,
    ):
        self.current_depth: int = 1  # Start from 1 and increment up to total_depth
        self.total_depth: int = total_depth
        self.current_breadth: int = (
            0  # Start from 0 and count up to total_breadth as queries complete
        )
        self.total_breadth: int = total_breadth
        self.current_query: str | None = None
        self.total_queries: int = 0
        self.completed_queries: int = 0


class DeepResearchSkill:
    def __init__(
        self,
        researcher: GPTResearcher,
    ):
        self.researcher: GPTResearcher = researcher
        self.breadth: int = researcher.cfg.DEEP_RESEARCH_BREADTH
        self.concurrency_limit: int = getattr(
            researcher.cfg, "DEEP_RESEARCH_CONCURRENCY", 2
        )
        self.config_path: Path | None = (
            researcher.cfg.config_path
            if hasattr(researcher.cfg, "config_path")
            else None
        )
        self.context: list[str] = []  # Track all context
        self.depth: int = researcher.cfg.DEEP_RESEARCH_DEPTH
        self.headers: dict[str, str] = researcher.headers or {}
        self.learnings: list[str] = []
        self.research_sources: list[dict[str, Any]] = []  # Track all research sources
        self.tone: Tone = researcher.tone
        self.visited_urls: set[str] = researcher.visited_urls
        self.websocket: WebSocket | CustomLogsHandler | None = researcher.websocket
        self.max_context_words: int = researcher.cfg.MAX_CONTEXT_WORDS
        self.num_queries: int = researcher.cfg.DEEP_RESEARCH_NUM_QUERIES
        self.num_learnings: int = researcher.cfg.DEEP_RESEARCH_NUM_LEARNINGS

    async def generate_search_queries(
        self,
        query: str,
        num_queries: int | None = None,
    ) -> list[dict[str, str]]:
        """Generate SERP queries for research."""
        if num_queries is None:
            num_queries = self.num_queries

        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": "You are an expert researcher generating search queries.",
            },
            {
                "role": "user",
                "content": f"Given the following prompt, generate {num_queries} unique search queries to research the topic thoroughly. For each query, provide a research goal. Format as 'Query: <query>' followed by 'Goal: <goal>' for each pair: {query}",
            },
        ]

        response: str = await create_chat_completion(
            messages=messages,
            llm_provider=self.researcher.cfg.STRATEGIC_LLM_PROVIDER,
            model=self.researcher.cfg.STRATEGIC_LLM_MODEL,
            reasoning_effort="medium",
            temperature=0.4,
        )

        lines: list[str] = response.split("\n")
        queries: list[dict[str, str]] = []
        current_query: dict[str, str] = {}

        for line in lines:
            line = line.strip()
            if line.startswith("Query:"):
                if current_query:
                    queries.append(current_query)
                current_query = {"query": line.replace("Query:", "").strip()}
            elif line.startswith("Goal:") and current_query:
                current_query["researchGoal"] = line.replace("Goal:", "").strip()

        if current_query:
            queries.append(current_query)

        return queries[:num_queries]

    async def generate_research_plan(
        self,
        query: str,
        num_questions: int | None = None,
    ) -> list[str]:
        """Generate follow-up questions to clarify research direction."""
        if num_questions is None:
            num_questions = self.num_queries

        # Get initial search results to inform query generation
        search_results: list[dict[str, Any]] = await get_search_results(
            query, self.researcher.retrievers[0]
        )
        logger.info(f"Initial web knowledge obtained: {len(search_results)} results")

        # Get current time for context
        current_time: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": "You are an expert researcher. Your task is to analyze the original query and search results, then generate targeted questions that explore different aspects and time periods of the topic.",
            },
            {
                "role": "user",
                "content": f"""Original query: {query}

Current time: {current_time}

Search results:
{search_results}

Based on these results, the original query, and the current time, generate {num_questions} unique questions. Each question should explore a different aspect or time period of the topic, considering recent developments up to {current_time}.

Format each question on a new line starting with 'Question: '""",
            },
        ]

        response: str = await create_chat_completion(
            messages=messages,
            llm_provider=self.researcher.cfg.STRATEGIC_LLM_PROVIDER,
            model=self.researcher.cfg.STRATEGIC_LLM_MODEL,
            reasoning_effort=ReasoningEfforts.High.value,
            temperature=0.4,
        )

        questions: list[str] = [
            q.replace("Question:", "").strip()
            for q in response.split("\n")
            if q.strip().startswith("Question:")
        ]
        return questions[:num_questions]

    async def process_research_results(
        self,
        query: str,
        context: str,
        num_learnings: int | None = None,
    ) -> dict[str, Any]:
        """Process research results to extract learnings and follow-up questions."""
        if num_learnings is None:
            num_learnings = self.num_learnings

        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": "You are an expert researcher analyzing search results.",
            },
            {
                "role": "user",
                "content": f"Given the following research results for the query '{query}', extract key learnings and suggest follow-up questions. For each learning, include a citation to the source URL if available. Format each learning as 'Learning [source_url]: <insight>' and each question as 'Question: <question>':\n\n{context}",
            },
        ]

        response: str = await create_chat_completion(
            messages=messages,
            llm_provider=self.researcher.cfg.STRATEGIC_LLM_PROVIDER,
            model=self.researcher.cfg.STRATEGIC_LLM_MODEL,
            temperature=0.4,
            reasoning_effort=ReasoningEfforts.High.value,
            max_tokens=1000,
        )

        lines: list[str] = response.split("\n")
        learnings: list[str] = []
        questions: list[str] = []
        citations: dict[str, str] = {}

        for line in lines:
            line: str = line.strip()
            if line.startswith("Learning"):
                import re

                url_match = re.search(r"\[(.*?)\]:", line)
                if url_match:
                    url: str = url_match.group(1)
                    learning: str = line.split(":", 1)[1].strip()
                    learnings.append(learning)
                    citations[learning] = url
                else:
                    # Try to find URL in the line itself
                    url_match: re.Match[str] | None = re.search(
                        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                        line,
                    )
                    if url_match:
                        url = url_match.group(0)
                        learning = (
                            line.replace(url, "").replace("Learning:", "").strip()
                        )
                        learnings.append(learning)
                        citations[learning] = url
                    else:
                        learnings.append(line.replace("Learning:", "").strip())
            elif line.startswith("Question:"):
                questions.append(line.replace("Question:", "").strip())

        return {
            "learnings": learnings[:num_learnings],
            "followUpQuestions": questions[:num_learnings],
            "citations": citations,
        }

    async def deep_research(
        self,
        query: str,
        breadth: int,
        depth: int,
        learnings: list[str] | None = None,
        citations: dict[str, str] | None = None,
        visited_urls: set[str] | None = None,
        on_progress: Callable[[ResearchProgress], None] | None = None,
    ) -> dict[str, Any]:
        """Conduct deep iterative research."""
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
        serp_queries: list[dict[str, str]] = await self.generate_search_queries(
            query, num_queries=breadth
        )
        progress.total_queries = len(serp_queries)

        all_learnings: list[str] = learnings.copy()
        all_citations: dict[str, str] = citations.copy()
        all_visited_urls: set[str] = visited_urls.copy()
        all_context: list[str] = []
        all_sources: list[dict[str, Any]] = []

        # Process queries with concurrency limit
        semaphore = asyncio.Semaphore(self.concurrency_limit)

        async def process_query(serp_query: dict[str, str]) -> dict[str, Any] | None:
            async with semaphore:
                try:
                    progress.current_query = serp_query["query"]
                    if on_progress:
                        on_progress(progress)

                    from gpt_researcher.agent import GPTResearcher

                    researcher = GPTResearcher(
                        query=serp_query["query"],
                        report_type=ReportType.ResearchReport.value,
                        report_source=ReportSource.Web.value,
                        tone=self.tone,
                        websocket=self.websocket,
                        config_path=self.config_path,
                        headers=self.headers,
                        visited_urls=self.visited_urls,
                    )

                    # Conduct research
                    context: list[str] = await researcher.conduct_research()

                    # Get results and visited URLs
                    visited: set[str] = researcher.visited_urls
                    sources: list[dict[str, Any]] = researcher.research_sources

                    # Process results to extract learnings and citations
                    results: dict[str, Any] = await self.process_research_results(
                        query=serp_query["query"],
                        context="\n".join(context),
                        num_learnings=self.num_learnings,
                    )

                    # Update progress
                    progress.completed_queries += 1
                    progress.current_breadth += 1
                    if on_progress:
                        on_progress(progress)

                    return {
                        "learnings": results["learnings"],
                        "visited_urls": list(visited),
                        "followUpQuestions": results["followUpQuestions"],
                        "researchGoal": serp_query["researchGoal"],
                        "citations": results["citations"],
                        "context": context if context else "",
                        "sources": sources if sources else [],
                    }

                except Exception as e:
                    logger.error(
                        f"Error processing query '{serp_query['query']}': {str(e)}"
                    )
                    return None

        # Process queries concurrently with limit
        tasks: list[Coroutine[Any, Any, dict[str, Any] | None]] = [
            process_query(query) for query in serp_queries
        ]
        results: list[dict[str, Any] | None] = await asyncio.gather(*tasks)
        filtered_results: list[dict[str, Any]] = [r for r in results if r is not None]

        # Update breadth progress based on successful queries
        progress.current_breadth = len(filtered_results)
        if on_progress:
            on_progress(progress)

        # Collect all results
        for result in filtered_results:
            all_learnings.extend(result["learnings"])
            all_visited_urls.update(result["visited_urls"])
            all_citations.update(result["citations"])
            if result["context"]:
                all_context.append(result["context"])
            if result["sources"]:
                all_sources.extend(result["sources"])

            # Continue deeper if needed
            if depth > 1:
                new_breadth: int = max(2, breadth // 2)
                new_depth: int = depth - 1
                progress.current_depth += 1

                # Create next query from research goal and follow-up questions
                next_query: str = f"""
                Previous research goal: {result["researchGoal"]}
                Follow-up questions: {" ".join(result["followUpQuestions"])}"""

                # Recursive research
                deeper_results: dict[str, Any] = await self.deep_research(
                    query=next_query,
                    breadth=new_breadth,
                    depth=new_depth,
                    learnings=all_learnings,
                    citations=all_citations,
                    visited_urls=all_visited_urls,
                    on_progress=on_progress,
                )

                all_learnings: list[str] = deeper_results["learnings"]
                all_visited_urls.update(deeper_results["visited_urls"])
                all_citations.update(deeper_results["citations"])
                if deeper_results.get("context"):
                    all_context.extend(deeper_results["context"])
                if deeper_results.get("sources"):
                    all_sources.extend(deeper_results["sources"])

        # Update class tracking
        self.context.extend(all_context)
        self.research_sources.extend(all_sources)

        # Trim context to stay within word limits
        trimmed_context: list[str] = trim_context_to_word_limit(
            all_context, max_words=self.max_context_words
        )
        logger.info(
            f"Trimmed context from {len(all_context)} items to {len(trimmed_context)} items to stay within word limit"
        )

        return {
            "learnings": list(set(all_learnings)),
            "visited_urls": list(all_visited_urls),
            "citations": all_citations,
            "context": trimmed_context,
            "sources": all_sources,
        }

    async def run(
        self,
        on_progress: Callable[[ResearchProgress], None] | None = None,
    ) -> list[str]:
        """Run the deep research process and generate final report."""
        start_time: float = time.time()

        # Log initial costs
        initial_costs: float = self.researcher.get_costs()

        follow_up_questions: list[str] = await self.generate_research_plan(
            self.researcher.query
        )
        answers: list[str] = ["Automatically proceeding with research"] * len(
            follow_up_questions
        )

        qa_pairs: list[str] = [
            f"Q: {q}\nA: {a}" for q, a in zip(follow_up_questions, answers)
        ]
        combined_query: str = f"""
        Initial Query: {self.researcher.query}\nFollow - up Questions and Answers:\n
        """ + "\n".join(qa_pairs)

        results: dict[str, Any] = await self.deep_research(
            query=combined_query,
            breadth=self.breadth,
            depth=self.depth,
            on_progress=on_progress,
        )

        # Get costs after deep research
        research_costs: float = self.researcher.get_costs() - initial_costs

        # Log research costs if we have a log handler
        if self.researcher.log_handler:
            await self.researcher._log_event(
                "research",
                step="deep_research_costs",
                details={
                    "research_costs": research_costs,
                    "total_costs": self.researcher.get_costs(),
                },
            )

        # Prepare context with citations
        context_with_citations: list[str] = []
        for learning in results["learnings"]:
            citation: str = results["citations"].get(learning, "")
            if citation:
                context_with_citations.append(f"{learning} [Source: {citation}]")
            else:
                context_with_citations.append(learning)

        # Add all research context
        if results.get("context"):
            context_with_citations.extend(results["context"])

        # Trim final context to word limit
        final_context: list[str] = trim_context_to_word_limit(context_with_citations)

        # Set enhanced context and visited URLs
        self.researcher.context = final_context
        self.researcher.visited_urls = results["visited_urls"]

        # Set research sources
        if results.get("sources"):
            self.researcher.research_sources = results["sources"]

        # Log total execution time
        end_time: float = time.time()
        execution_time: timedelta = timedelta(seconds=end_time - start_time)
        logger.info(f"Total research execution time: {execution_time}")
        logger.info(f"Total research costs: ${research_costs:.2f}")

        # Return the context - don't generate report here as it will be done by the main agent
        return self.researcher.context
