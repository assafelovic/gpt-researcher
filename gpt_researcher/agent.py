from __future__ import annotations

import json
import logging
import os

from typing import TYPE_CHECKING, Any, ClassVar, Coroutine

from langchain_core.documents import Document

from gpt_researcher.actions.agent_creator import choose_agent
from gpt_researcher.actions.markdown_processing import (
    add_references,
    extract_headers,
    extract_sections,
    table_of_contents,
)
from gpt_researcher.actions.retriever import get_retrievers
from gpt_researcher.config import Config
from gpt_researcher.llm_provider import GenericLLMProvider
from gpt_researcher.memory import Memory
from gpt_researcher.skills.browser import BrowserManager
from gpt_researcher.skills.context_manager import ContextManager
from gpt_researcher.skills.curator import SourceCurator
from gpt_researcher.skills.researcher import ResearchConductor
from gpt_researcher.skills.writer import ReportGenerator
from gpt_researcher.utils.schemas import Subtopics
from gpt_researcher.utils.enum import (
    OutputFileType,
    ReportFormat,
    ReportSource,
    ReportType,
    Tone,
)
from gpt_researcher.vector_store import VectorStoreWrapper

if TYPE_CHECKING:
    from backend.server.server_utils import CustomLogsHandler
    from fastapi.websockets import WebSocket
    from langchain_community.vectorstores import VectorStore
    from langchain_core.retrievers import BaseRetriever

    from gpt_researcher.utils.schemas import LogHandler


class GPTResearcher:
    logger: ClassVar[logging.Logger] = logging.getLogger(__name__)

    def __init__(
        self,
        query: str,
        report_type: ReportType | str | None = ReportType.ResearchReport.value,
        report_format: ReportFormat | str | None = ReportFormat.APA.value,
        output_file_type: OutputFileType = OutputFileType.MARKDOWN,
        report_source: ReportSource | str | None = ReportSource.Web.value,
        tone: Tone | str | None = None,
        source_urls: list[str] | None = None,
        document_urls: list[str] | None = None,
        documents: list[dict[str, Any] | Document] | None = None,
        complement_source_urls: bool = False,
        vector_store: VectorStore | None = None,
        vector_store_filter: dict[str, Any] | None = None,
        config: Config | dict[str, Any] | os.PathLike | str | None = None,
        websocket: WebSocket | CustomLogsHandler | None = None,
        agent_role: str | None = None,
        parent_query: str = "",
        subtopics: list[str] | None = None,
        visited_urls: set[str] | None = None,
        verbose: bool = True,
        context: list[str] | None = None,
        headers: dict[str, str] | None = None,
        max_subtopics: int = 10,
        log_handler: LogHandler | None = None,
        research_images: list[dict[str, Any]] | None = None,
        research_sources: list[dict[str, Any]] | None = None,
        query_domains: list[str] = [],
        config_path: os.PathLike | str | None = None,
    ):
        self.query: str = query
        self.cfg: Config = Config()
        if config is None:
            self.cfg = Config(config_path)  # For backwards compatibility
        elif isinstance(config, dict):
            self.cfg = Config.from_config(config)
        elif isinstance(config, (str, os.PathLike)):
            self.cfg = Config.from_path(config)
        else:
            raise ValueError(f"Invalid config type: `{config.__class__.__name__}`")

        self.report_type = ReportType.OutlineReport if report_type is None else ReportType(report_type)
        self.report_source = ReportSource.Web if report_source is None else ReportSource(report_source)
        self.report_format = ReportFormat.APA if report_format is None else ReportFormat(report_format)
        self.output_format = output_file_type
        self.max_subtopics = max_subtopics
        self.tone = (
            tone
            if isinstance(tone, Tone)
            else (
                Tone.__members__[tone]
                if (tone or "").strip() and tone is not None
                else Tone.Objective
            )
        )
        self.source_urls: list[str] = [] if source_urls is None else source_urls
        self.document_urls: list[str] = [] if document_urls is None else document_urls
        self.complement_source_urls: bool = complement_source_urls
        self.query_domains: list[str] = query_domains
        self.research_images: list[dict[str, Any]] = [] if research_images is None else research_images
        self.research_sources: list[dict[str, Any]] = [] if research_sources is None else research_sources
        self.documents: list[dict[str, Any]] = []
        if documents is not None:
            for document in documents:
                if isinstance(document, Document):
                    self.documents.append(document.model_dump())
                else:
                    self.documents.append(document)
        self.vector_store: VectorStoreWrapper | None = (
            None
            if vector_store is None
            else VectorStoreWrapper(vector_store)
        )
        self.vector_store_filter: dict[str, Any] | None = vector_store_filter
        self.websocket: CustomLogsHandler | WebSocket | None = websocket
        self.agent_role = agent_role if agent_role else ""
        self.parent_query: str = parent_query
        self.subtopics: list[str] = [] if subtopics is None else subtopics
        self.visited_urls: set[str] = set() if visited_urls is None else visited_urls
        self.verbose = verbose

        self.context: list[str] = [] if context is None else context
        self.headers: dict[str, str] = {} if headers is None else headers
        self.research_costs: float = 0.0
        self.retrievers: list[type[BaseRetriever]] = get_retrievers(
            self.headers,
            self.cfg,
        )
        self.memory: Memory = Memory(
            self.cfg.EMBEDDING_PROVIDER,
            self.cfg.EMBEDDING_MODEL,
            **self.cfg.EMBEDDING_KWARGS,
        )
        self.log_handler: LogHandler | None = log_handler
        self.llm: GenericLLMProvider = GenericLLMProvider(self.smart_llm)  # For backwards compatibility

        # Initialize components
        self.research_conductor: ResearchConductor = ResearchConductor(self)
        self.report_generator: ReportGenerator = ReportGenerator(self)
        self.context_manager: ContextManager = ContextManager(self)
        self.scraper_manager: BrowserManager = BrowserManager(self)
        self.source_curator: SourceCurator = SourceCurator(self)

    async def _log_event(
        self,
        event_type: str,
        **kwargs,
    ):
        """Helper method to handle logging events."""
        if self.log_handler:
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

                # Add direct logging as backup
                import logging

                research_logger: logging.Logger = logging.getLogger("research")
                research_logger.info(f"{event_type}: {json.dumps(kwargs, default=str)}")

            except Exception as e:
                import logging

                self.logger.exception(f"Error in _log_event: {e.__class__.__name__}: {e}")

    async def conduct_research(self) -> list[str]:
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

        if not (self.agent and self.agent_role):
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

    async def write_report(
        self,
        existing_headers: list[dict[str, Any]] | None = None,
        relevant_written_contents: list[str] | None = None,
        ext_context: list[str] | None = None,
    ) -> str:
        existing_headers = [] if existing_headers is None else existing_headers
        relevant_written_contents = [] if relevant_written_contents is None else relevant_written_contents
        ext_context = [] if ext_context is None else ext_context

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
            ext_context="\n".join(ext_context or self.context) if ext_context else "",
        )

        await self._log_event(
            "research",
            step="report_completed",
            details={"report_length": len(report)},
        )
        return report

    async def write_report_conclusion(
        self,
        report_body: str,
    ) -> str:
        await self._log_event("research", step="writing_conclusion")
        conclusion = await self.report_generator.write_report_conclusion(report_body)
        await self._log_event("research", step="conclusion_completed")
        return conclusion

    async def write_introduction(
        self,
    ) -> str:
        await self._log_event("research", step="writing_introduction")
        intro = await self.report_generator.write_introduction()
        await self._log_event("research", step="introduction_completed")
        return intro

    async def get_subtopics(
        self,
    ) -> list[str] | Subtopics:
        return await self.report_generator.get_subtopics()

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
        self.verbose = verbose

    def add_costs(
        self,
        cost: float,
    ):
        if not isinstance(cost, (float, int)):
            raise ValueError("Cost must be an integer or float")
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
    def verbose(self) -> bool:
        return self.cfg.VERBOSE

    @verbose.setter
    def verbose(self, value: bool):
        self.cfg.VERBOSE = value

    @property
    def tone(self) -> Tone:
        return self.cfg.TONE

    @tone.setter
    def tone(self, value: Tone | str):
        self.cfg.TONE = (
            value
            if isinstance(value, Tone)
            else Tone.__members__[value.capitalize()]
        )

    @property
    def report_type(self) -> ReportType:
        return self.cfg.REPORT_TYPE

    @report_type.setter
    def report_type(self, value: ReportType | str):
        self.cfg.REPORT_TYPE = (
            value
            if isinstance(value, ReportType)
            else ReportType.__members__[value]
        )

    @property
    def report_format(self) -> ReportFormat:
        return self.cfg.REPORT_FORMAT

    @report_format.setter
    def report_format(self, value: ReportFormat | str):
        self.cfg.REPORT_FORMAT = (
            value
            if isinstance(value, ReportFormat)
            else ReportFormat.__members__[value]
        )

    @property
    def report_source(self) -> ReportSource:
        return self.cfg.REPORT_SOURCE

    @report_source.setter
    def report_source(self, value: ReportSource | str):
        self.cfg.REPORT_SOURCE = (
            value
            if isinstance(value, ReportSource)
            else ReportSource.__members__[value]
        )

    @property
    def output_format(self) -> OutputFileType:
        return self.cfg.OUTPUT_FORMAT

    @output_format.setter
    def output_format(self, value: OutputFileType | str):
        self.cfg.OUTPUT_FORMAT = (
            value
            if isinstance(value, OutputFileType)
            else OutputFileType.__members__[value.upper()]
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
