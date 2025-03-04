from __future__ import annotations

import json
import logging
import os

from typing import TYPE_CHECKING, Any, Callable, ClassVar, Coroutine

from langchain_core.documents import Document

from gpt_researcher.actions.agent_creator import choose_agent
from gpt_researcher.actions.markdown_processing import add_references, extract_headers, extract_sections, table_of_contents
from gpt_researcher.actions.retriever import get_retrievers
from gpt_researcher.config import Config
from gpt_researcher.llm_provider import GenericLLMProvider
from gpt_researcher.memory import Memory
from gpt_researcher.skills.browser import BrowserManager
from gpt_researcher.skills.context_manager import ContextManager
from gpt_researcher.skills.deep_research import DeepResearchSkill
from gpt_researcher.skills.curator import SourceCurator
from gpt_researcher.skills.researcher import ResearchConductor
from gpt_researcher.skills.writer import ReportGenerator
from gpt_researcher.utils.enum import OutputFileType, ReportFormat, ReportSource, ReportType, Tone
from gpt_researcher.vector_store import VectorStoreWrapper
from skills.deep_research import ResearchProgress

if TYPE_CHECKING:
    from backend.server.server_utils import CustomLogsHandler, HTTPStreamAdapter
    from fastapi.websockets import WebSocket
    from langchain_community.vectorstores import VectorStore


class GPTResearcher:
    logger: ClassVar[logging.Logger] = logging.getLogger("gpt_researcher")

    def __init__(
        self,
        query: str,
        report_type: ReportType | str | None = ReportType.ResearchReport.value,
        report_format: OutputFileType | str | None = OutputFileType.MARKDOWN.value,
        report_source: ReportSource | str | None = ReportSource.Web.value,
        tone: Tone | str | None = Tone.Objective.value,
        source_urls: list[str] | None = None,
        document_urls: list[str] | None = None,
        complement_source_urls: bool = False,
        query_domains: list[str] | None = None,
        documents: list[dict[str, Any] | Document] | None = None,
        vector_store: VectorStore | None = None,
        vector_store_filter: dict[str, Any] | None = None,
        config: Config | dict[str, Any] | os.PathLike | str | None = None,
        websocket: WebSocket | HTTPStreamAdapter | CustomLogsHandler | None = None,
        agent_role: str | None = None,
        parent_query: str = "",
        subtopics: list[str] | None = None,
        visited_urls: set[str] | None = None,
        verbose: bool = True,
        context: list[str] | None = None,
        headers: dict[str, str] | None = None,
        max_subtopics: int = 5,
        log_handler: CustomLogsHandler | None = None,
        config_path: os.PathLike | str | None = None,
        **kwargs,
    ):
        self.cfg: Config = config if isinstance(config, Config) else Config(VERBOSE=verbose, **kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)
        if config_path is not None:
            self.cfg.__dict__.update(Config.from_path(config_path).to_dict())
        if isinstance(config, (os.PathLike, str)):
            self.cfg.__dict__.update(Config.from_path(config).to_dict())
        elif isinstance(config, dict):
            self.cfg.__dict__.update(config)
        elif config is not None:
            raise ValueError(f"Invalid config type: {config.__class__.__name__} with contents: {config}")

        self.query: str = query
        self.source_urls: list[str] = [] if source_urls is None else source_urls
        self.document_urls: list[str] = [] if document_urls is None else document_urls
        self.complement_source_urls: bool = complement_source_urls
        self.query_domains: list[str] = [] if query_domains is None else query_domains
        self.research_images: list[dict[str, Any]] = []
        self.research_sources: list[dict[str, Any]] = []
        self.documents: list[dict[str, Any]] = [
            document.model_dump()
            if isinstance(document, Document)
            else document
            for document in (tuple() if documents is None else documents)
        ]
        self.vector_store: VectorStoreWrapper | None = None if vector_store is None else VectorStoreWrapper(vector_store)
        self.vector_store_filter: dict[str, Any] = {} if vector_store_filter is None else vector_store_filter
        self.websocket: CustomLogsHandler | WebSocket | HTTPStreamAdapter | None = websocket
        self.parent_query: str = parent_query
        self.subtopics: list[str] = [] if subtopics is None else subtopics
        self.visited_urls: set[str] = set() if visited_urls is None else visited_urls

        self.context: list[str] = [] if context is None else context
        self.headers: dict[str, str] = {} if headers is None else headers
        self.research_costs: float = 0.0
        self.retrievers: list[type] = get_retrievers(self.headers, self.cfg)
        self.memory: Memory = Memory(
            self.cfg.EMBEDDING_PROVIDER,
            self.cfg.EMBEDDING_MODEL,
            **self.cfg.EMBEDDING_KWARGS,
        )
        self.log_handler: CustomLogsHandler | None = log_handler
        self.llm: GenericLLMProvider = GenericLLMProvider(
            self.cfg.SMART_LLM,
            fallback_models=self.cfg.FALLBACK_MODELS,
        )

        # deprecated arguments, it's recommended to use Config objects instead of passing a billion parameters to GPTResearcher.
        self.agent_role = self.cfg.AGENT_ROLE if agent_role is None else agent_role
        self.max_subtopics = self.cfg.MAX_SUBTOPICS if max_subtopics is None else max_subtopics
        self.output_format = self.cfg.OUTPUT_FORMAT if report_format is None else report_format
        self.report_source = self.cfg.REPORT_SOURCE if report_source is None else report_source
        self.report_type = self.cfg.REPORT_TYPE if report_type is None else report_type
        self.tone = self.cfg.TONE if tone is None else tone

        # Initialize components
        self.research_conductor: ResearchConductor = ResearchConductor(self)
        self.report_generator: ReportGenerator = ReportGenerator(self)
        self.context_manager: ContextManager = ContextManager(self)
        self.scraper_manager: BrowserManager = BrowserManager(self)
        self.source_curator: SourceCurator = SourceCurator(self)
        self.deep_researcher: DeepResearchSkill | None = None
        if report_type == ReportType.DeepResearch.value:
            self.deep_researcher = DeepResearchSkill(self)

    async def _log_event(
        self,
        event_type: str,
        **kwargs: Any,
    ):
        """Helper method to handle logging events.

        Args:
            event_type: Type of event to log (tool, action, research, logs, images)
            **kwargs: Additional data to include in the log event
        """
        if self.log_handler is not None:
            try:
                if event_type == "tool":
                    await self.log_handler.on_tool_start(kwargs.get("tool_name", ""), **kwargs)
                elif event_type == "action":
                    await self.log_handler.on_agent_action(kwargs.get("action", ""), **kwargs)
                elif event_type == "research":
                    await self.log_handler.on_research_step(kwargs.get("step", ""), kwargs.get("details", {}))
                elif event_type == "logs":
                    await self.log_handler.on_logs(
                        kwargs.get("content", ""),
                        kwargs.get("output", ""),
                        kwargs.get("metadata", {}),
                    )
                elif event_type == "images":
                    await self.log_handler.on_images(kwargs.get("images", []))

                import logging

                research_logger: logging.Logger = logging.getLogger("research")
                research_logger.info(f"{event_type}: {json.dumps(kwargs, default=str)}")

            except (ValueError, TypeError, KeyError) as e:
                import logging

                self.logger.exception(f"Error in _log_event: {e.__class__.__name__}: {e}")

    async def conduct_research(
        self,
        on_progress: Callable[[ResearchProgress], None] | None = None,
    ) -> list[str]:
        research_details: dict[str, Any] = {
            "query": self.query,
            "agent": self.agent,
            "report_type": self.report_type,
            "role": self.agent_role,
        }
        log_event_result: Coroutine[Any, Any, Any] | None = self._log_event(
            "research",
            step="start",
            details=research_details,
        )
        if log_event_result is not None and isinstance(log_event_result, Coroutine):
            await log_event_result

        # Handle deep research separately
        if self.report_type == ReportType.DeepResearch.value and self.deep_researcher:
            return await self._handle_deep_research(on_progress)

        if not (self.agent and self.role):
            await self._log_event("action", action="choose_agent")
            self.agent, self.agent_role = await choose_agent(
                query=self.query,
                cfg=self.cfg,
                parent_query=self.parent_query,
                cost_callback=self.add_costs,
                headers=self.headers,  # Pass headers to choose_agent?
            )
            await self._log_event(
                "action",
                action="agent_selected",
                details={"agent": self.agent, "role": self.agent_role},
            )

        await self._log_event(
            "research",
            step="conducting_research",
            details={"agent": self.agent, "role": self.agent_role},
        )
        research_result: str | list[str] = await self.research_conductor.conduct_research()
        self.context = [research_result] if isinstance(research_result, str) else research_result

        await self._log_event(
            "research",
            step="research_completed",
            details={
                "context_length": len(self.context),
                "context": self.context,
            },
        )
        return self.context

    async def _handle_deep_research(
        self,
        on_progress: Callable[[ResearchProgress], None] | None = None,
    ) -> list[str]:
        """Handle deep research execution and logging."""
        # Log deep research configuration
        assert self.deep_researcher is not None
        await self._log_event(
            "research",
            step="deep_research_initialize",
            details={
                "type": "deep_research",
                "breadth": self.deep_researcher.breadth,
                "depth": self.deep_researcher.depth,
                "concurrency": self.deep_researcher.concurrency_limit,
            },
        )

        # Log deep research start
        await self._log_event(
            "research",
            step="deep_research_start",
            details={
                "query": self.query,
                "breadth": self.deep_researcher.breadth,
                "depth": self.deep_researcher.depth,
                "concurrency": self.deep_researcher.concurrency_limit,
            },
        )

        # Run deep research and get context
        assert self.deep_researcher is not None
        result: str = await self.deep_researcher.run(on_progress=on_progress)
        self.context = result.split("\n")

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
        return self.context

    async def write_report(
        self,
        existing_headers: list[dict[str, Any]] | None = None,
        relevant_written_contents: list[str] | None = None,
        external_context: list[str] | None = None,
    ) -> str:
        """Generate a report based on research context.

        Returns:
            str: The generated report
        """
        existing_headers = [] if existing_headers is None else existing_headers
        relevant_written_contents = [] if relevant_written_contents is None else relevant_written_contents
        external_context = [] if external_context is None else external_context

        await self._log_event(
            "research",
            step="writing_report",
            details={
                "existing_headers": existing_headers,
                "context_source": "external" if external_context else "internal",
                #                "context": self.context,
                #                "ext_context": ext_context,
                #                "relevant_written_contents": relevant_written_contents,
            },
        )

        report: str = await self.report_generator.write_report(
            existing_headers=existing_headers,
            relevant_written_contents=relevant_written_contents,
            ext_context="\n".join(external_context or self.context) if external_context else "",
        )

        await self._log_event(
            "research",
            step="report_completed",
            details={
                "report_length": len(report),
                "report": report,
            },
        )
        return report

    async def write_report_conclusion(
        self,
        report_body: str,
    ) -> str:
        await self._log_event("research", step="writing_conclusion")
        conclusion = await self.report_generator.write_report_conclusion(report_body)
        await self._log_event("research", step="conclusion_completed", details={"conclusion": conclusion})
        return conclusion

    async def write_introduction(
        self,
    ) -> str:
        await self._log_event("research", step="writing_introduction")
        intro = await self.report_generator.write_introduction()
        await self._log_event("research", step="introduction_completed", details={"introduction": intro})
        return intro

    async def get_draft_section_titles(
        self,
        current_subtopic: str,
    ) -> list[str]:
        return await self.report_generator.get_draft_section_titles(current_subtopic)

    async def get_similar_written_contents_by_draft_section_titles(
        self,
        current_subtopic: str,
        draft_section_titles: list[str],
        written_contents: list[str],
        max_results: int = 10,
    ) -> list[str]:
        return await self.context_manager.get_similar_written_contents_by_draft_section_titles(
            current_subtopic,
            draft_section_titles,
            written_contents,
            max_results,
        )

    # Utility methods
    def get_research_images(
        self,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        return self.research_images[:top_k]

    def add_research_images(
        self,
        images: list[dict[str, Any]],
    ):
        self.research_images.extend(images)

    def get_research_sources(self) -> list[dict[str, Any]]:
        return self.research_sources

    def add_research_sources(
        self,
        sources: list[dict[str, Any]],
    ):
        self.research_sources.extend(sources)

    def add_references(
        self,
        report_markdown: str,
        visited_urls: set[str],
    ) -> str:
        return add_references(report_markdown, visited_urls)

    def extract_headers(
        self,
        markdown_text: str,
    ) -> list[dict[str, Any]]:
        return extract_headers(markdown_text)

    def extract_sections(
        self,
        markdown_text: str,
    ) -> list[dict[str, Any]]:
        return extract_sections(markdown_text)

    def table_of_contents(
        self,
        markdown_text: str,
    ) -> str:
        return table_of_contents(markdown_text)

    def get_source_urls(self) -> list[str]:
        return list(self.visited_urls)

    def get_research_context(self) -> list[str]:
        return self.context

    def get_costs(self) -> float:
        return self.research_costs

    def set_verbose(
        self,
        verbose: bool,
    ):
        self.cfg.VERBOSE = verbose

    def add_costs(
        self,
        cost: float,
    ):
        self.research_costs += cost
        if self.log_handler is None:
            return
        _: Coroutine[Any, Any, None] = self._log_event(
            "research",
            step="cost_update",
            details={"cost": cost, "total_cost": self.research_costs},
        )

    @property
    def max_subtopics(self) -> int:
        return self.cfg.MAX_SUBTOPICS

    @max_subtopics.setter
    def max_subtopics(self, value: int):
        self.cfg.MAX_SUBTOPICS = value

    @property
    def agent(self) -> str:
        return self.cfg.AGENT_ROLE

    @agent.setter
    def agent(self, value: str):
        self.cfg.AGENT_ROLE = value

    @property
    def tone(self) -> Tone:
        return self.cfg.TONE

    @tone.setter
    def tone(self, value: Tone | str | None):
        self.cfg.TONE = (
            Tone.Objective
            if value is None
            else Tone.__members__[value.capitalize()]
            if isinstance(value, str) and value.capitalize() in Tone.__members__
            else value
            if isinstance(value, Tone)
            else Tone(value)
        )

    @property
    def report_type(self) -> ReportType:
        return self.cfg.REPORT_TYPE

    @report_type.setter
    def report_type(self, value: ReportType | str):
        self.cfg.REPORT_TYPE = (
            ReportType.__members__[value.replace("_", " ").title().replace(" ", "")]
            if isinstance(value, str) and value.replace("_", " ").title().replace(" ", "") in ReportType.__members__
            else value
            if isinstance(value, ReportType)
            else ReportType(value)
        )

    @property
    def report_format(self) -> ReportFormat:
        return self.cfg.REPORT_FORMAT

    @report_format.setter
    def report_format(self, value: ReportFormat | str):
        self.cfg.REPORT_FORMAT = (
            ReportFormat.__members__[value.upper()]
            if isinstance(value, str) and value.upper() in ReportFormat.__members__
            else value
            if isinstance(value, ReportFormat)
            else ReportFormat(value)
        )

    @property
    def report_source(self) -> ReportSource:
        return self.cfg.REPORT_SOURCE

    @report_source.setter
    def report_source(self, value: ReportSource | str):
        self.cfg.REPORT_SOURCE = (
            ReportSource.__members__[value]
            if isinstance(value, str) and value in ReportSource.__members__
            else value
            if isinstance(value, ReportSource)
            else ReportSource(value)
        )

    @property
    def output_format(self) -> OutputFileType:
        return self.cfg.OUTPUT_FORMAT

    @output_format.setter
    def output_format(self, value: OutputFileType | str):
        self.cfg.OUTPUT_FORMAT = (
            OutputFileType.__members__[value]
            if isinstance(value, str) and value in OutputFileType.__members__
            else value
            if isinstance(value, OutputFileType)
            else OutputFileType(value)
        )

    @property
    def curate_sources(self) -> bool:
        return self.cfg.CURATE_SOURCES

    @curate_sources.setter
    def curate_sources(self, value: bool):
        self.cfg.CURATE_SOURCES = value

    @property
    def agent_role(self) -> str:
        return self.cfg.AGENT_ROLE

    @agent_role.setter
    def agent_role(self, value: str):
        self.cfg.AGENT_ROLE = value

    @property
    def smart_llm(self) -> str:
        return self.cfg.SMART_LLM

    @smart_llm.setter
    def smart_llm(self, value: str):
        self.cfg.SMART_LLM = value

    @property
    def post_retrieval_processing_instructions(self) -> str:
        return self.cfg.POST_RETRIEVAL_PROCESSING_INSTRUCTIONS

    @post_retrieval_processing_instructions.setter
    def post_retrieval_processing_instructions(self, value: str):
        self.cfg.POST_RETRIEVAL_PROCESSING_INSTRUCTIONS = value
