from typing import Optional, List, Dict, Any, Set
import json

from .config import Config
from .memory import Memory
from .utils.enum import ReportSource, ReportType, Tone
from .llm_provider import GenericLLMProvider
from .vector_store import VectorStoreWrapper

# Research skills
from .skills.researcher import ResearchConductor
from .skills.writer import ReportGenerator
from .skills.context_manager import ContextManager
from .skills.browser import BrowserManager
from .skills.curator import SourceCurator

from .actions import (
    add_references,
    extract_headers,
    extract_sections,
    table_of_contents,
    get_retrievers,
    choose_agent
)


class GPTResearcher:
    def __init__(
        self,
        query: str,
        report_type: str = ReportType.ResearchReport.value,
        report_format: str = "markdown",
        report_source: str = ReportSource.Web.value,
        tone: Tone = Tone.Objective,
        source_urls=None,
        document_urls=None,
        complement_source_urls=False,
        documents=None,
        vector_store=None,
        vector_store_filter=None,
        config_path=None,
        websocket=None,
        agent=None,
        role=None,
        parent_query: str = "",
        subtopics: list = [],
        visited_urls: set = set(),
        verbose: bool = True,
        context=[],
        headers: dict = None,
        max_subtopics: int = 5,
        log_handler=None,
    ):
        self.query = query
        self.report_type = report_type
        self.cfg = Config(config_path)
        self.llm = GenericLLMProvider(self.cfg)
        self.report_source = getattr(
            self.cfg, 'report_source', None) or report_source
        self.report_format = report_format
        self.max_subtopics = max_subtopics
        self.tone = tone if isinstance(tone, Tone) else Tone.Objective
        self.source_urls = source_urls
        self.document_urls = document_urls
        self.complement_source_urls: bool = complement_source_urls
        self.research_sources = []  # The list of scraped sources including title, content and images
        self.research_images = []  # The list of selected research images
        self.documents = documents
        self.vector_store = VectorStoreWrapper(vector_store) if vector_store else None
        self.vector_store_filter = vector_store_filter
        self.websocket = websocket
        self.agent = agent
        self.role = role
        self.parent_query = parent_query
        self.subtopics = subtopics
        self.visited_urls = visited_urls
        self.verbose = verbose
        self.context = context
        self.headers = headers or {}
        self.research_costs = 0.0
        self.retrievers = get_retrievers(self.headers, self.cfg)
        self.memory = Memory(
            self.cfg.embedding_provider, self.cfg.embedding_model, **self.cfg.embedding_kwargs
        )
        self.log_handler = log_handler

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
                    await self.log_handler.on_tool_start(kwargs.get('tool_name', ''), **kwargs)
                elif event_type == "action":
                    await self.log_handler.on_agent_action(kwargs.get('action', ''), **kwargs)
                elif event_type == "research":
                    await self.log_handler.on_research_step(kwargs.get('step', ''), kwargs.get('details', {}))
                
                # Add direct logging as backup
                import logging
                research_logger = logging.getLogger('research')
                research_logger.info(f"{event_type}: {json.dumps(kwargs, default=str)}")
                
            except Exception as e:
                import logging
                logging.getLogger('research').error(f"Error in _log_event: {e}", exc_info=True)

    async def conduct_research(self):
        await self._log_event("research", step="start", details={
            "query": self.query,
            "report_type": self.report_type,
            "agent": self.agent,
            "role": self.role
        })

        if not (self.agent and self.role):
            await self._log_event("action", action="choose_agent")
            self.agent, self.role = await choose_agent(
                query=self.query,
                cfg=self.cfg,
                parent_query=self.parent_query,
                cost_callback=self.add_costs,
                headers=self.headers,
            )
            await self._log_event("action", action="agent_selected", details={
                "agent": self.agent,
                "role": self.role
            })

        await self._log_event("research", step="conducting_research", details={
            "agent": self.agent,
            "role": self.role
        })
        self.context = await self.research_conductor.conduct_research()
        
        await self._log_event("research", step="research_completed", details={
            "context_length": len(self.context)
        })
        return self.context

    async def write_report(self, existing_headers: list = [], relevant_written_contents: list = [], ext_context=None) -> str:
        await self._log_event("research", step="writing_report", details={
            "existing_headers": existing_headers,
            "context_source": "external" if ext_context else "internal"
        })
        
        report = await self.report_generator.write_report(
            existing_headers,
            relevant_written_contents,
            ext_context or self.context
        )
        
        await self._log_event("research", step="report_completed", details={
            "report_length": len(report)
        })
        return report

    async def write_report_conclusion(self, report_body: str) -> str:
        await self._log_event("research", step="writing_conclusion")
        conclusion = await self.report_generator.write_report_conclusion(report_body)
        await self._log_event("research", step="conclusion_completed")
        return conclusion

    async def write_introduction(self):
        await self._log_event("research", step="writing_introduction")
        intro = await self.report_generator.write_introduction()
        await self._log_event("research", step="introduction_completed")
        return intro

    async def get_subtopics(self):
        return await self.report_generator.get_subtopics()

    async def get_draft_section_titles(self, current_subtopic: str):
        return await self.report_generator.get_draft_section_titles(current_subtopic)

    async def get_similar_written_contents_by_draft_section_titles(
        self,
        current_subtopic: str,
        draft_section_titles: List[str],
        written_contents: List[Dict],
        max_results: int = 10
    ) -> List[str]:
        return await self.context_manager.get_similar_written_contents_by_draft_section_titles(
            current_subtopic,
            draft_section_titles,
            written_contents,
            max_results
        )

    # Utility methods
    def get_research_images(self, top_k=10) -> List[Dict[str, Any]]:
        return self.research_images[:top_k]

    def add_research_images(self, images: List[Dict[str, Any]]) -> None:
        self.research_images.extend(images)

    def get_research_sources(self) -> List[Dict[str, Any]]:
        return self.research_sources

    def add_research_sources(self, sources: List[Dict[str, Any]]) -> None:
        self.research_sources.extend(sources)

    def add_references(self, report_markdown: str, visited_urls: set) -> str:
        return add_references(report_markdown, visited_urls)

    def extract_headers(self, markdown_text: str) -> List[Dict]:
        return extract_headers(markdown_text)

    def extract_sections(self, markdown_text: str) -> List[Dict]:
        return extract_sections(markdown_text)

    def table_of_contents(self, markdown_text: str) -> str:
        return table_of_contents(markdown_text)

    def get_source_urls(self) -> list:
        return list(self.visited_urls)

    def get_research_context(self) -> list:
        return self.context

    def get_costs(self) -> float:
        return self.research_costs

    def set_verbose(self, verbose: bool):
        self.verbose = verbose

    def add_costs(self, cost: float) -> None:
        if not isinstance(cost, (float, int)):
            raise ValueError("Cost must be an integer or float")
        self.research_costs += cost
        if self.log_handler:
            self._log_event("research", step="cost_update", details={
                "cost": cost,
                "total_cost": self.research_costs
            })
