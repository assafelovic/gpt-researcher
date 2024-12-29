"""Controller for managing research operations."""

from __future__ import annotations

import loguru
import os

from typing import TYPE_CHECKING

from gpt_researcher.agent import GPTResearcher
from gpt_researcher.utils.enum import ReportType, Tone

if TYPE_CHECKING:
    from standalone_app.app import GPTResearcherApp

logger = loguru.logger


class ResearchController:
    """Controls research operations and state."""

    def __init__(self, app: GPTResearcherApp):
        """Initialize the research controller."""
        self.app: GPTResearcherApp = app
        self.researcher: GPTResearcher | None = None
        self.is_researching: bool = False
        self._costs: float = 0.0
        self._sources: list[str] = []

    async def start_research(
        self,
        query: str,
        report_type: str,
        tone: str | Tone,
        source: str,
        curate_sources: bool = False,
        search_engine: str = "duckduckgo",
        num_sources: int = 5,
        tavily_api_key: str | None = None,
    ) -> str:
        """Start a new research task.

        Args:
            query: The research query
            report_type: Type of report to generate
            tone: Tone of the report
            source: Source of research data
            curate_sources: Whether to carefully check and filter sources
            search_engine: Search engine to use
            num_sources: Number of sources to use
            tavily_api_key: Optional Tavily API key

        Returns:
            The research report text
        """
        # Map selections to enum values
        report_type_map = {
            "Summary - Short and fast (~2 min)": ReportType.ResearchReport.value,
            "Detailed - In depth and longer (~5 min)": ReportType.DetailedReport.value,
            "Resource Report": ReportType.ResourceReport.value,
        }
        source_map = {"The Web": "web", "My Documents": "local", "Hybrid": "hybrid"}

        try:
            self.is_researching = True

            # Update config with current settings
            config = self.app.settings_manager.get_config()
            config_path = str(self.app.paths.config / "settings.json")

            # Update config settings for this research session
            os.environ["RETRIEVER"] = search_engine
            os.environ["MAX_SEARCH_RESULTS_PER_QUERY"] = str(num_sources)
            os.environ["CURATE_SOURCES"] = str(curate_sources).lower()

            # Set Tavily API key if provided
            if tavily_api_key and search_engine.lower() == "tavily":
                os.environ["TAVILY_API_KEY"] = tavily_api_key

            # Create researcher with our config path
            self.researcher = GPTResearcher(
                query=query,
                report_type=report_type_map[report_type],
                tone=Tone[tone] if isinstance(tone, str) else tone,
                report_source=source_map[source],
                verbose=True,
                config_path=config_path,  # Pass the config file path
            )

            # Conduct research
            _context = await self.researcher.conduct_research()

            # Generate report
            report = await self.researcher.write_report()

            # Get metadata
            self._sources = self.researcher.get_source_urls()
            self._costs = self.researcher.get_costs()

            # Create formatted report
            output = "Research Report\n"
            output += "=" * 80 + "\n\n"
            output += report + "\n\n"

            output += "Sources\n"
            output += "-" * 80 + "\n"
            for i, source in enumerate(self._sources, 1):
                output += f"{i}. {source}\n"

            output += "\n" + "-" * 80 + "\n"
            output += f"Total cost: ${self._costs:.4f}"

            return output

        except Exception as e:
            logger.exception("Error during research")
            raise ResearchError(f"Research failed: {str(e)}") from e

        finally:
            self.is_researching = False

    def stop_research(self):
        """Stop the current research task."""
        # TODO: Implement this
        pass

    def get_research_data(self) -> dict[str, str | float | list[str]]:
        """Get the current research data.

        Returns:
            Dictionary containing research metadata
        """
        return {"costs": self._costs, "sources": self._sources}


class ResearchError(Exception):
    """Exception raised for errors during research."""

    pass
