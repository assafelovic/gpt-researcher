from __future__ import annotations

import asyncio
import os

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from gpt_researcher import GPTResearcher
from gpt_researcher.config.config import Config
from gpt_researcher.config.variables.base import BaseConfig
from gpt_researcher.llm_provider.generic.base import ReasoningEfforts
from gpt_researcher.utils.enum import ReportSource, ReportType, Tone
from gpt_researcher.utils.llm import create_chat_completion

if TYPE_CHECKING:
    import logging

    from fastapi import WebSocket

    from backend.server.server_utils import CustomLogsHandler

logger: logging.Logger = logging.getLogger(__name__)


class ResearchProgress:
    def __init__(
        self,
        total_depth: int,
        total_breadth: int,
    ):
        self.current_depth: int = total_depth
        self.total_depth: int = total_depth
        self.current_breadth: int = total_breadth
        self.total_breadth: int = total_breadth
        self.current_query: str | None = None
        self.total_queries: int = 0
        self.completed_queries: int = 0


class DeepResearch:
    def __init__(
        self,
        query: str,
        breadth: int = 4,
        depth: int = 2,
        websocket: WebSocket | CustomLogsHandler | None = None,
        tone: Tone = Tone.Objective,
        config_path: str | None = None,
        headers: dict[str, str] | None = None,
        concurrency_limit: int = 2,  # Match TypeScript version
        config: Config | None = None,
    ):
        self.config_path: Path | None = None if config_path is None else Path(os.path.normpath(config_path))
        cfg: BaseConfig | Config = (
            Config.load_config(self.config_path)
            if self.config_path is not None
            else config
            if config is not None
            else Config()
        )
        if isinstance(cfg, dict):
            cfg = Config()
            cfg._set_attributes(cfg)
        self.cfg: Config = cfg
        self.query: str = query
        self.breadth: int = breadth
        self.depth: int = depth
        self.websocket: WebSocket | CustomLogsHandler | None = websocket
        self.tone: Tone = tone
        self.headers: dict[str, str] | None = headers or {}
        self.visited_urls: set[str] = set()
        self.learnings: list[str] = []
        self.concurrency_limit: int = concurrency_limit

    async def generate_feedback(
        self,
        query: str,
        num_questions: int = 3,
    ) -> list[str]:
        """Generate follow-up questions to clarify research direction."""
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": "You are an expert researcher helping to clarify research directions.",
            },
            {
                "role": "user",
                "content": f"Given the following query from the user, ask some follow up questions to clarify the research direction. Return a maximum of {num_questions} questions, but feel free to return less if the original query is clear. Format each question on a new line starting with 'Question: ': {query}",
            },
        ]

        response: str = await create_chat_completion(
            messages=messages,
            llm_provider=self.cfg.strategic_llm_provider,  # pyright: ignore[reportAttributeAccess]
            model=self.cfg.strategic_llm_model,  # pyright: ignore[reportAttributeAccess]
            temperature=0.7,
#            max_tokens=500,
            reasoning_effort=ReasoningEfforts.High.value,
            cfg=self.cfg,
        )

        # Parse questions from response
        questions: list[str] = [q.replace("Question:", "").strip() for q in response.split("\n") if q.strip().startswith("Question:")]
        return questions[:num_questions]

    async def generate_serp_queries(
        self,
        query: str,
        num_queries: int = 3,
    ) -> list[dict[str, str]]:
        """Generate SERP queries for research."""
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
            llm_provider=self.cfg.smart_llm_provider,  # pyright: ignore[reportAttributeAccess]
            model=self.cfg.smart_llm_model,  # pyright: ignore[reportAttributeAccess]
            temperature=0.7,
#            max_tokens=1000,
            cfg=self.cfg,
        )

        # Parse queries and goals from response
        lines: list[str] = response.split("\n")
        queries: list[dict[str, str]] = []
        current_query: dict[str, str] = {}

        for line in lines:
            line: str = line.strip()
            if line.startswith("Query:"):
                if current_query:
                    queries.append(current_query)
                current_query = {"query": line.replace("Query:", "").strip()}
            elif line.startswith("Goal:"):
                current_query["researchGoal"] = line.replace("Goal:", "").strip()

        if current_query:
            queries.append(current_query)

        return queries[:num_queries]

    async def process_serp_result(
        self,
        query: str,
        context: str,
        num_learnings: int = 3,
    ) -> dict[str, Any]:
        """Process research results to extract learnings and follow-up questions."""
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": "You are an expert researcher analyzing search results.",
            },
            {
                "role": "user",
                "content": f"Given the following research results for the query '''{query}''', extract key learnings and suggest follow-up questions. For each learning, include a citation to the source URL if available. Format each learning as 'Learning [source_url]: <insight>' and each question as 'Question: <question>':\n\n{context}",
            },
        ]

        response: str = await create_chat_completion(
            messages=messages,
            llm_provider=self.cfg.smart_llm_provider,  # pyright: ignore[reportAttributeAccess]
            model=self.cfg.smart_llm_model,  # pyright: ignore[reportAttributeAccess]
            temperature=0.7,
#            max_tokens=1000,
            reasoning_effort=ReasoningEfforts.High.value,
            cfg=self.cfg,
        )

        # Parse learnings and questions with citations
        lines: list[str] = response.split("\n")
        learnings: list[str] = []
        questions: list[str] = []
        citations: dict[str, str] = {}

        for line in lines:
            line: str = line.strip()
            if line.startswith("Learning"):
                # Extract URL if present in square brackets
                import re

                url_match: re.Match | None = re.search(r"\[(.*?)\]:", line)
                if url_match:
                    url: str = url_match.group(1)
                    learning: str = line.split(":", 1)[1].strip()
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
        on_progress=None,
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
        serp_queries: list[dict[str, str]] = await self.generate_serp_queries(query, num_queries=breadth)
        progress.total_queries = len(serp_queries)

        all_learnings: list[str] = learnings.copy()
        all_citations: dict[str, str] = citations.copy()
        all_visited_urls: set[str] = visited_urls.copy()

        # Process queries with concurrency limit
        semaphore = asyncio.Semaphore(self.concurrency_limit)

        async def process_query(serp_query: dict[str, str]) -> dict[str, Any] | None:
            async with semaphore:
                try:
                    progress.current_query = serp_query["query"]
                    if on_progress:
                        on_progress(progress)

                    # Initialize researcher for this query
                    researcher = GPTResearcher(
                        query=serp_query["query"],
                        report_type=ReportType.ResearchReport.value,
                        report_source=ReportSource.Web.value,
                        tone=self.tone,
                        websocket=self.websocket,
                        headers=self.headers,
                    )
                    researcher.cfg = self.cfg

                    # Conduct research
                    await researcher.conduct_research()

                    # Get results
                    visited: set[str] = set(researcher.visited_urls)

                    # Process results
                    results: dict[str, Any] = await self.process_serp_result(
                        query=serp_query["query"],
                        context="\n".join(researcher.context) if isinstance(researcher.context, list) else researcher.context,
                    )

                    # Update progress
                    progress.completed_queries += 1
                    if on_progress is not None:
                        on_progress(progress)

                    return {
                        "learnings": results["learnings"],
                        "visited_urls": visited,
                        "followUpQuestions": results["followUpQuestions"],
                        "researchGoal": serp_query["researchGoal"],
                        "citations": results["citations"],
                    }

                except Exception as e:
                    logger.error(f"Error processing query '{serp_query['query']}': {str(e)}")
                    return None

        # Process queries concurrently with limit
        tasks: list[Coroutine[Any, Any, dict[str, Any] | None]] = [process_query(query) for query in serp_queries]
        results: list[dict[str, Any] | None] = await asyncio.gather(*tasks)
        filtered_results: list[dict[str, Any]] = [r for r in results if r is not None]  # Filter out failed queries

        # Collect all results
        for result in filtered_results:
            all_learnings.extend(result["learnings"])
            all_visited_urls.update(set(result["visited_urls"]))
            all_citations.update(result["citations"])

            # Continue deeper if needed
            if depth > 1:
                new_breadth: int = max(2, breadth // 2)
                new_depth: int = depth - 1

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

                all_learnings = deeper_results["learnings"]
                all_visited_urls = set(deeper_results["visited_urls"])
                all_citations.update(deeper_results["citations"])

        return {
            "learnings": list(set(all_learnings)),
            "visited_urls": list(all_visited_urls),
            "citations": all_citations,
        }

    async def run(
        self,
        on_progress: Callable[[ResearchProgress], None] | None = None,
    ) -> str:
        """Run the deep research process and generate final report."""
        # Get initial feedback
        follow_up_questions: list[str] = await self.generate_feedback(self.query)

        # Collect answers (this would normally come from user interaction)
        answers: list[str] = ["Automatically proceeding with research"] * len(follow_up_questions)

        # Combine query and Q&A
        follow_up_qa: str = " ".join(
            [
                f"Q: {q}\nA: {a}"
                for q, a in zip(follow_up_questions, answers)
            ]
        )
        combined_query: str = f"""
        Initial Query: {self.query}
        Follow-up Questions and Answers:
        {follow_up_qa}"""

        # Run deep research
        results: dict[str, Any] = await self.deep_research(
            query=combined_query,
            breadth=self.breadth,
            depth=self.depth,
            on_progress=on_progress,
        )

        # Generate final report
        researcher = GPTResearcher(
            query=self.query,
            report_type=ReportType.DetailedReport.value,
            report_source=ReportSource.Web.value,
            tone=self.tone,
            websocket=self.websocket,
            headers=self.headers,
        )
        researcher.cfg = self.cfg

        # Prepare context with citations
        context_with_citations: list[str] = []
        for learning in results["learnings"]:
            citation: str = results["citations"].get(learning, "")
            if citation:
                context_with_citations.append(f"{learning} [Source: {citation}]")
            else:
                context_with_citations.append(learning)

        # Set enhanced context for final report
        researcher.context = context_with_citations
        researcher.visited_urls = set(results["visited_urls"])

        # Generate report
        report: str = await researcher.write_report()
        return report
