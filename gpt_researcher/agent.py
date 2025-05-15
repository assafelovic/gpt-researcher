from __future__ import annotations

import json
from typing import Any

from gpt_researcher.actions import (
    add_references,
    choose_agent,
    extract_headers,
    extract_sections,
    get_retrievers,
    get_search_results,
    table_of_contents,
)
from gpt_researcher.config import Config
from gpt_researcher.llm_provider import GenericLLMProvider
from gpt_researcher.memory import Memory
from gpt_researcher.prompts import get_prompt_family
from gpt_researcher.skills.browser import BrowserManager
from gpt_researcher.skills.context_manager import ContextManager
from gpt_researcher.skills.curator import SourceCurator

# Research skills
from gpt_researcher.skills.researcher import ResearchConductor
from gpt_researcher.skills.writer import ReportGenerator
from gpt_researcher.utils.enum import ReportSource, ReportType, Tone
from gpt_researcher.vector_store import VectorStoreWrapper


class GPTResearcher:
    def __init__(
        self,
        query: str,
        report_type: str = ReportType.ResearchReport.value,
        report_format: str = "markdown",
        report_source: str = ReportSource.Web.value,
        tone: Tone = Tone.Objective,
        source_urls: list[str] | None = None,
        document_urls: list[str] | None = None,
        complement_source_urls: bool = False,
        documents: list[dict[str, Any]] | None = None,
        vector_store: VectorStoreWrapper | None = None,
        vector_store_filter: list[str] | None = None,
        config_path: str | None = None,
        websocket: Any | None = None,
        agent: str | None = None,
        role: str | None = None,
        parent_query: str = "",
        subtopics: list[str] | None = None,
        visited_urls: set[str] | None = None,
        verbose: bool = True,
        context: list[dict[str, Any]] | None = None,
        headers: dict | None = None,
        max_subtopics: int = 5,
        log_handler: Any | None = None,
        prompt_family: str | None = None,
    ):
        self.query: str = query
        self.report_type: str = report_type
        self.cfg: Config = Config(config_path)
        self.cfg.set_verbose(verbose)
        self.llm: GenericLLMProvider = GenericLLMProvider(self.cfg)
        self.report_source: str = (
            report_source if report_source else getattr(self.cfg, "report_source", "")
        )
        self.report_format: str = report_format
        self.max_subtopics: int = max_subtopics
        self.tone: Tone = tone if isinstance(tone, Tone) else Tone.Objective
        self.source_urls: list[str] = [] if source_urls is None else source_urls
        self.document_urls: list[str] = [] if document_urls is None else document_urls
        self.complement_source_urls: bool = complement_source_urls
        self.research_sources: list[
            dict[str, Any]
        ] = []  # The list of scraped sources including title, content and images
        self.research_images: list[
            dict[str, Any]
        ] = []  # The list of selected research images
        self.documents: list[dict[str, Any]] = [] if documents is None else documents
        self.vector_store: VectorStoreWrapper | None = (
            VectorStoreWrapper(vector_store) if vector_store else None
        )
        self.vector_store_filter: list[str] | None = vector_store_filter
        self.websocket: Any | None = websocket
        self.agent: str | None = agent
        self.role: str | None = role
        self.parent_query: str = parent_query
        self.subtopics: list[str] | None = subtopics
        self.visited_urls: set[str] = set() if visited_urls is None else visited_urls
        self.verbose: bool = verbose
        self.context: list[dict[str, Any]] | None = context
        self.headers: dict | None = headers
        self.research_costs: float = 0.0
        self.retrievers: list[Any] = get_retrievers(self.headers, self.cfg)
        self.memory: Memory = Memory(
            self.cfg.embedding_provider,
            self.cfg.embedding_model,
            **self.cfg.embedding_kwargs,
        )
        self.log_handler: Any | None = log_handler
        self.prompt_family: Any = get_prompt_family(
            prompt_family or self.cfg.prompt_family, self.cfg
        )

        # Initialize components
        self.research_conductor: ResearchConductor = ResearchConductor(self)
        self.report_generator: ReportGenerator = ReportGenerator(self)
        self.context_manager: ContextManager = ContextManager(self)
        self.scraper_manager: BrowserManager = BrowserManager(self)
        self.source_curator: SourceCurator = SourceCurator(self)

    async def _log_event(self, event_type: str, **kwargs):
        """Helper method to handle logging events"""
        if self.log_handler:
            try:
                if event_type == "tool":
                    await self.log_handler.on_tool_start(
                        kwargs.get("tool_name", ""), **kwargs
                    )
                elif event_type == "action":
                    await self.log_handler.on_agent_action(
                        kwargs.get("action", ""), **kwargs
                    )
                elif event_type == "research":
                    await self.log_handler.on_research_step(
                        kwargs.get("step", ""), kwargs.get("details", {})
                    )

                # Add direct logging as backup
                import logging

                research_logger = logging.getLogger("research")
                research_logger.info(f"{event_type}: {json.dumps(kwargs, default=str)}")

            except Exception as e:
                import logging

                logging.getLogger("research").error(
                    f"Error in _log_event: {e.__class__.__name__}: {e}", exc_info=True
                )

    async def conduct_research(self) -> list[dict[str, Any]]:
        await self._log_event(
            "research",
            step="start",
            details={
                "query": self.query,
                "report_type": self.report_type,
                "agent": self.agent,
                "role": self.role,
            },
        )

        if not (self.agent and self.role):
            await self._log_event("action", action="choose_agent")
            self.agent, self.role = await choose_agent(
                query=self.query,
                cfg=self.cfg,
                parent_query=self.parent_query,
                cost_callback=self.add_costs,
                headers=self.headers,
                prompt_family=self.prompt_family,
            )
            await self._log_event(
                "action",
                action="agent_selected",
                details={"agent": self.agent, "role": self.role},
            )

        await self._log_event(
            "research",
            step="conducting_research",
            details={"agent": self.agent, "role": self.role},
        )
        self.context = await self.research_conductor.conduct_research()

        await self._log_event(
            "research",
            step="research_completed",
            details={"context_length": len(self.context)},
        )
        return self.context or []

    async def write_report(
        self,
        existing_headers: list[str] | None = None,
        relevant_written_contents: list[str] | None = None,
        ext_context: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        await self._log_event(
            "research",
            step="writing_report",
            details={
                "existing_headers": existing_headers,
                "context_source": "external" if ext_context else "internal",
            },
        )

        await self.report_generator.write_report(
            existing_headers,
            relevant_written_contents,
            ext_context or self.context,
        )

        # Run deep research and get context
        self.context = await self.deep_researcher.run(on_progress=on_progress)

        # Get total research costs
        total_costs: float = self.get_costs()

        # Log deep research completion with costs
        await self._log_event(
            "research",
            step="deep_research_complete",
            details={
                "context_length": len(self.context),
                "visited_urls": len(self.visited_urls),
                "total_costs": total_costs,
            },
        )

        # Log final cost update
        await self._log_event(
            "research",
            step="cost_update",
            details={
                "cost": total_costs,
                "total_cost": total_costs,
                "research_type": "deep_research",
            },
        )

        # Return the research context
        return self.context or []

    async def write_report(
        self,
        existing_headers: list[str] | None = None,
        relevant_written_contents: list[str] | None = None,
        ext_context: list[dict[str, Any]] | None = None,
        custom_prompt: str = "",
    ) -> str:
        await self._log_event(
            "research",
            step="writing_report",
            details={
                "existing_headers": existing_headers,
                "context_source": "external" if ext_context else "internal",
            },
        )

        report: str = await self.report_generator.write_report(
            existing_headers=existing_headers,
            relevant_written_contents=relevant_written_contents,
            ext_context=ext_context or self.context,
            custom_prompt=custom_prompt,
        )

        await self._log_event(
            "research",
            step="report_completed",
            details={
                "report_length": len(report),
            },
        )
        return report

    async def write_report_conclusion(self, report_body: str) -> str:
        await self._log_event("research", step="writing_conclusion")
        conclusion: str = await self.report_generator.write_report_conclusion(report_body)
        await self._log_event("research", step="conclusion_completed")
        return conclusion

    async def write_introduction(self) -> str:
        await self._log_event("research", step="writing_introduction")
        intro: str = await self.report_generator.write_introduction()
        await self._log_event("research", step="introduction_completed")
        return intro

    async def quick_search(
        self,
        query: str,
        query_domains: list[str] | None = None,
    ) -> list[Any]:
        return await get_search_results(
            query,
            self.retrievers[0],
            query_domains=query_domains,
        )

    async def get_subtopics(self) -> list[str]:
        return await self.report_generator.get_subtopics()

    async def get_draft_section_titles(self, current_subtopic: str) -> list[str]:
        return await self.report_generator.get_draft_section_titles(current_subtopic)

    async def get_similar_written_contents_by_draft_section_titles(
        self,
        current_subtopic: str,
        draft_section_titles: list[str],
        written_contents: list[dict[str, Any]],
        max_results: int = 10,
    ) -> list[str]:
        return await self.context_manager.get_similar_written_contents_by_draft_section_titles(
            current_subtopic,
            draft_section_titles,
            written_contents,
            max_results,
        )

    # Utility methods
    def get_research_images(self, top_k: int = 10) -> list[dict[str, Any]]:
        return self.research_images[:top_k]

    def add_research_images(self, images: list[dict[str, Any]]) -> None:
        self.research_images.extend(images)

    def get_research_sources(self) -> list[dict[str, Any]]:
        return self.research_sources

    def add_research_sources(self, sources: list[dict[str, Any]]) -> None:
        self.research_sources.extend(sources)

    def add_references(
        self,
        report_markdown: str,
        visited_urls: set,
    ) -> str:
        return add_references(report_markdown, visited_urls)

    def extract_headers(self, markdown_text: str) -> list[dict[str, Any]]:
        return extract_headers(markdown_text)

    def extract_sections(self, markdown_text: str) -> list[dict[str, Any]]:
        return extract_sections(markdown_text)

    def table_of_contents(self, markdown_text: str) -> str:
        return table_of_contents(markdown_text)

    def get_source_urls(self) -> list[str]:
        return list(self.visited_urls)

    def get_research_context(self) -> list[dict[str, Any]]:
        return self.context or []

    def get_costs(self) -> float:
        return self.research_costs

    def set_verbose(self, verbose: bool):
        self.verbose = verbose

    def add_costs(self, cost: float) -> None:
        if not isinstance(cost, (float, int)):
            raise ValueError("Cost must be an integer or float")
        self.research_costs += cost
        if self.log_handler:
            _ = self._log_event(
                "research",
                step="cost_update",
                details={"cost": cost, "total_cost": self.research_costs},
            )
