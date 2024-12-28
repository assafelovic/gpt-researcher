from __future__ import annotations

import os

from gpt_researcher.agent import GPTResearcher
from gpt_researcher.utils.enum import ReportType, Tone


class ResearchError(Exception):
    """Custom exception for research-related errors."""

    pass


class ResearchClient:
    def __init__(self):
        """Initialize the research client that interfaces directly with GPTResearcher."""
        # Check for required environment variables
        required_vars: list[str] = ["OPENAI_API_KEY", "TAVILY_API_KEY"]
        missing_vars: list[str] = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ResearchError(f"Missing required environment variables: {', '.join(missing_vars)}\n" "Please set these variables before starting the application.")

    async def submit_research(
        self,
        query: str,
        report_type: str = ReportType.ResearchReport.value,
    ) -> dict:
        """Submit a research query directly to GPTResearcher.

        Args:
            query: The research query to process
            report_type: Type of report to generate

        Returns:
            dict: The research results including report and metadata

        Raises:
            ResearchError: If there's an error during the research process
        """
        try:
            # Create researcher instance
            researcher = GPTResearcher(query=query, report_type=report_type, tone=Tone.Objective, verbose=True)

            # Conduct research
            context = await researcher.conduct_research()

            # Generate report
            report = await researcher.write_report()

            # Get metadata
            sources = researcher.get_source_urls()
            costs = researcher.get_costs()

            return {"report": report, "sources": sources, "costs": costs, "context": context}

        except Exception as e:
            raise ResearchError(f"Research failed: {str(e)}")
