
from __future__ import annotations

import json
import os
import time
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from litellm import cast
from numpy import roll
from pytest import warns

from gpt_researcher.actions import (
    add_references,
    choose_agent,
    extract_headers,
    extract_sections,
    get_retrievers,
    get_search_results,
    table_of_contents,
)

# from gpt_researcher.actions.report_analyzer import analyze_query_requirements, get_research_configuration
from gpt_researcher.actions.report_analyzer import analyze_query_requirements, get_research_configuration
from gpt_researcher.config import Config
from gpt_researcher.llm_provider import GenericLLMProvider

#from gpt_researcher.memory.embeddings import FallbackMemory
from gpt_researcher.memory.embeddings import Memory
from gpt_researcher.prompts import PromptFamily, get_prompt_family
from gpt_researcher.skills.browser import BrowserManager
from gpt_researcher.skills.context_manager import ContextManager
from gpt_researcher.skills.curator import SourceCurator
from gpt_researcher.skills.deep_research import DeepResearchSkill
from gpt_researcher.skills.llm_visualizer import enable_llm_visualization
from gpt_researcher.skills.researcher import ResearchConductor
from gpt_researcher.skills.structured_research import ResearchResults, StructuredResearchPipeline
from gpt_researcher.skills.writer import ReportGenerator
from gpt_researcher.utils.enum import ReportSource, ReportType, Tone
from gpt_researcher.utils.llm_debug_logger import get_llm_debug_logger, initialize_llm_debug_logger
from gpt_researcher.utils.schemas import LogHandler
from gpt_researcher.vector_store import VectorStoreWrapper

if TYPE_CHECKING:
    from fastapi import WebSocket

    from gpt_researcher.retrievers.retriever_abc import RetrieverABC


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
        query_domains: list[str] | None = None,
        documents: list[dict[str, Any]] | None = None,
        vector_store: VectorStoreWrapper | None = None,
        vector_store_filter: list[str] | None = None,
        config_path: str | None = None,
        websocket: WebSocket | None = None,
        agent: str | None = None,
        role: str | None = None,
        parent_query: str = "",
        subtopics: list[str] | None = None,
        visited_urls: set[str] | None = None,
        verbose: bool = True,
        context: list[str] | list[dict[str, Any]] | None = None,
        headers: dict[str, Any] | None = None,
        max_subtopics: int = 5,
        log_handler: LogHandler | None = None,
        prompt_family: str | None = None,
        mcp_configs: list[dict[str, Any]] | None = None,
        mcp_max_iterations: int | None = None,
        mcp_strategy: str | None = None,
        disable_structured_research: bool = True,
        **kwargs
    ):
        """Initialize a GPT Researcher instance.

        Args:
            query (str): The research query or question.
            report_type (str): Type of report to generate.
            report_format (str): Format of the report (markdown, pdf, etc).
            report_source (str): Source of information for the report (web, local, etc).
            tone (Tone): Tone of the report.
            source_urls (list[str], optional): List of specific URLs to use as sources.
            document_urls (list[str], optional): List of document URLs to use as sources.
            complement_source_urls (bool): Whether to complement source URLs with web search.
            query_domains (list[str], optional): List of domains to restrict search to.
            documents: Document objects for LangChain integration.
            vector_store: Vector store for document retrieval.
            vector_store_filter: Filter for vector store queries.
            config_path: Path to configuration file.
            websocket: WebSocket for streaming output.
            agent: Pre-defined agent type.
            role: Pre-defined agent role.
            parent_query: Parent query for subtopic reports.
            subtopics: List of subtopics to research.
            visited_urls: Set of already visited URLs.
            verbose (bool): Whether to output verbose logs.
            context: Pre-loaded research context.
            headers (dict, optional): Additional headers for requests and configuration.
            max_subtopics (int): Maximum number of subtopics to generate.
            log_handler: Handler for logging events.
            prompt_family: Family of prompts to use.
            mcp_configs (list[dict], optional): List of MCP server configurations.
                Each dictionary can contain:
                - name (str): Name of the MCP server
                - command (str): Command to start the server
                - args (list[str]): Arguments for the server command
                - tool_name (str): Specific tool to use on the MCP server
                - env (dict): Environment variables for the server
                - connection_url (str): URL for WebSocket or HTTP connection
                - connection_type (str): Connection type (stdio, websocket, http)
                - connection_token (str): Authentication token for remote connections

                Example:
                ```python
                mcp_configs=[{
                    "command": "python",
                    "args": ["my_mcp_server.py"],
                    "name": "search"
                }]
                ```
            mcp_strategy (str, optional): MCP execution strategy. Options:
                - "fast" (default): Run MCP once with original query for best performance
                - "deep": Run MCP for all sub-queries for maximum thoroughness
                - "disabled": Skip MCP entirely, use only web retrievers
            disable_structured_research (bool): Whether to disable structured research functionality.
        """
        self.kwargs = warns
        self.query: str = query
        self.report_type = report_type
        self.cfg: Config = Config(config_path)
        self.cfg.set_verbose(verbose)
        self.llm: GenericLLMProvider = GenericLLMProvider(self.cfg)
        self.report_type: ReportType | str = report_type
        self.report_source: ReportSource | str | None = report_source if report_source else getattr(self.cfg, "report_source", None)
        self.report_format: str = report_format
        self.max_subtopics: int = max_subtopics
        self.tone: Tone | str = Tone.Objective if tone is None else tone if isinstance(tone, Tone) else Tone(tone)
        self.source_urls: list[str] = [] if source_urls is None else source_urls
        self.document_urls: list[str] = [] if document_urls is None else document_urls
        self.complement_source_urls: bool = complement_source_urls
        self.query_domains: list[str] = [] if query_domains is None else query_domains
        self.research_sources: list[dict[str, Any]] = []  # The list of scraped sources including title, content and images
        self.research_images: list[dict[str, Any]] = []  # The list of selected research images
        self.documents: list[dict[str, Any]] = [] if documents is None else documents
        self.vector_store: VectorStoreWrapper | None = VectorStoreWrapper(vector_store) if vector_store else None
        self.vector_store_filter: list[str] | None = vector_store_filter
        self.websocket: WebSocket | None = websocket
        self.agent: str | None = agent
        self.role: str | None = roll
        self.parent_query: str = parent_query
        self.subtopics: list[str] | None = subtopics
        self.visited_urls: set[str] = set() if visited_urls is None else visited_urls
        self.verbose: bool = verbose
        self.context: list[str] | list[dict[str, Any]] | None = [] if context is None else context
        self.headers: dict[str, Any] | None = {} if headers is None else headers
        self.research_costs: float = 0.0
        self.log_handler: LogHandler | None = log_handler
        self.prompt_family: PromptFamily = get_prompt_family(
            prompt_family or self.cfg.prompt_family,  # pyright: ignore[reportAttributeAccessIssue]
            self.cfg,
        )
        self.disable_structured_research: bool = disable_structured_research

        # Initialize the LLM debug logger
        session_id: str = f"gptr_{int(time.time())}"
        initialize_llm_debug_logger(session_id=session_id)
        self.debug_logger = get_llm_debug_logger()
        print(f"🔍 LLM Debug Logger initialized for session: {session_id}")

        # Process MCP configurations if provided
        self.mcp_configs: list[dict[str, Any]] | None = mcp_configs
        if mcp_configs:
            self._process_mcp_configs(mcp_configs)

        self.retrievers: list[type[RetrieverABC]] = get_retrievers(self.headers, self.cfg)

        self.memory: Memory = Memory(
            self.cfg.embedding_provider,
            self.cfg.embedding_model,
            **self.cfg.embedding_kwargs,
        )

        # Set default encoding to utf-8
        self.encoding = kwargs.get('encoding', 'utf-8')

        # Initialize components
        self.research_conductor: ResearchConductor = ResearchConductor(self)
        self.report_generator: ReportGenerator = ReportGenerator(self)
        self.context_manager: ContextManager = ContextManager(self)
        self.scraper_manager: BrowserManager = BrowserManager(self)
        self.source_curator: SourceCurator = SourceCurator(self)
        self.deep_researcher: DeepResearchSkill | None = (
            DeepResearchSkill(self)
            if report_type == ReportType.DeepResearch.value
            else None
        )
        # Handle MCP strategy configuration with backwards compatibility
        self.mcp_strategy = self._resolve_mcp_strategy(mcp_strategy, mcp_max_iterations)

        # Initialize structured research pipeline
#        self.structured_pipeline: StructuredResearchPipeline | None = None
#        self.query_analysis: dict[str, Any] | None = None
#        self.research_config: dict[str, Any] | None = None


    def _resolve_mcp_strategy(
        self,
        mcp_strategy: str | None,
        mcp_max_iterations: int | None,
    ) -> str:
        """
        Resolve MCP strategy from various sources with backwards compatibility.

        Priority:
        1. Parameter mcp_strategy (new approach)
        2. Parameter mcp_max_iterations (backwards compatibility)
        3. Config MCP_STRATEGY
        4. Default "fast"

        Args:
            mcp_strategy: New strategy parameter
            mcp_max_iterations: Legacy parameter for backwards compatibility

        Returns:
            str: Resolved strategy ("fast", "deep", or "disabled")
        """
        # Priority 1: Use mcp_strategy parameter if provided
        if mcp_strategy is not None:
            # Support new strategy names
            if mcp_strategy in ["fast", "deep", "disabled"]:
                return mcp_strategy
            # Support old strategy names for backwards compatibility
            elif mcp_strategy == "optimized":
                import logging
                logging.getLogger(__name__).warning("mcp_strategy 'optimized' is deprecated, use 'fast' instead")
                return "fast"
            elif mcp_strategy == "comprehensive":
                import logging
                logging.getLogger(__name__).warning("mcp_strategy 'comprehensive' is deprecated, use 'deep' instead")
                return "deep"
            else:
                import logging
                logging.getLogger(__name__).warning(f"Invalid mcp_strategy '{mcp_strategy}', defaulting to 'fast'")
                return "fast"

        # Priority 2: Convert mcp_max_iterations for backwards compatibility
        if mcp_max_iterations is not None:
            import logging
            logging.getLogger(__name__).warning("mcp_max_iterations is deprecated, use mcp_strategy instead")

            if mcp_max_iterations == 0:
                return "disabled"
            elif mcp_max_iterations == 1:
                return "fast"
            elif mcp_max_iterations == -1:
                return "deep"
            else:
                # Treat any other number as fast mode
                return "fast"

        # Priority 3: Use config setting
        if hasattr(self.cfg, 'mcp_strategy'):
            config_strategy = self.cfg.mcp_strategy
            # Support new strategy names
            if config_strategy in ["fast", "deep", "disabled"]:
                return config_strategy
            # Support old strategy names for backwards compatibility
            elif config_strategy == "optimized":
                return "fast"
            elif config_strategy == "comprehensive":
                return "deep"

        # Priority 4: Default to fast
        return "fast"

    def _process_mcp_configs(
        self,
        mcp_configs: list[dict[str, Any]],
    ) -> None:
        """Process MCP configurations from a list of configuration dictionaries.

        This method handles converting the MCP configuration list into appropriate
        header entries for the retrievers.

        Args:
            mcp_configs (list[dict[str, Any]]): List of MCP server configuration dictionaries.
                Each dictionary can contain keys like:
                - server_name: Name of the MCP server
                - server_command: Command to start the MCP server
                - server_args: List of arguments or string of arguments for the server command
                - tool_name: Name of the MCP tool to invoke
                - env: Dictionary of environment variables for the MCP server
        """
        # Check if user explicitly set RETRIEVER environment variable
        user_set_retriever: bool = os.getenv("RETRIEVER") is not None

        if not user_set_retriever:
            # Only auto-add MCP if user hasn't explicitly set retrievers
            if hasattr(self.cfg, 'retrievers') and self.cfg.retrievers:
                # If retrievers is set in config (but not via env var)
                current_retrievers: set[str] = (
                    set(self.cfg.retrievers.split(","))
                    if isinstance(self.cfg.retrievers, str)
                    else set(self.cfg.retrievers)
                )
                if "mcp" not in current_retrievers:
                    current_retrievers.add("mcp")
                    self.cfg.retrievers = ",".join(filter(None, current_retrievers))
            else:
                # No retrievers configured, use mcp as default
                self.cfg.retrievers = "mcp"
        # If user explicitly set RETRIEVER, respect their choice and don't auto-add MCP

        # Store the mcp_configs for use by the MCP retriever
        self.mcp_configs = mcp_configs

    async def _log_event(
        self,
        event_type: str,
        **kwargs,
    ) -> None:
        """Helper method to handle logging events"""
        if self.log_handler is not None:
            try:
                if event_type == "tool":
                    await self.log_handler.on_tool_start(kwargs.get("tool_name", ""), **kwargs)
                elif event_type == "action":
                    await self.log_handler.on_agent_action(kwargs.get("action", ""), **kwargs)
                elif event_type == "research":
                    await self.log_handler.on_research_step(kwargs.get("step", ""), kwargs.get("details", {}))

                # Add direct logging as backup
                import logging

                research_logger: logging.Logger = logging.getLogger("research")
                research_logger.info(f"{event_type}: {json.dumps(kwargs, default=str)}")

            except Exception as e:
                import logging

                logging.getLogger("research").error(
                    f"Error in _log_event: {e.__class__.__name__}: {e}",
                    exc_info=True,
                )

    async def conduct_research(
        self,
        on_progress: Callable[[str], None] | None = None,
    ) -> list[str]:
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

        # Handle deep research separately
        if (
            self.report_type == ReportType.DeepResearch.value
            and self.deep_researcher is not None
        ):
            return await self._handle_deep_research(on_progress)

        # Analyze query requirements for structured research only if not disabled
        if (
            not self.disable_structured_research
            and not self.query_analysis
        ):
            await self._log_event("action", action="analyze_query")
            self.query_analysis: dict[str, Any] | None = await analyze_query_requirements(
                query=self.query,
                cfg=self.cfg,
                cost_callback=self.add_costs,
            )
            self.research_config: dict[str, Any] | None = get_research_configuration(self.query_analysis)

            await self._log_event(
                "action",
                action="query_analyzed",
                details={
                    "report_style": self.query_analysis.get("report_style"),
                    "user_expertise": self.query_analysis.get("user_expertise"),
                    "enable_structured": self.research_config.get("enable_structured_research"),
                },
            )

        if (
            not self.agent
            or not self.agent.strip()
            or not self.role
            or not self.role.strip()
        ):
            await self._log_event("action", action="choose_agent")
            self.agent, self.role = await choose_agent(
                query=self.query,
                cfg=self.cfg,
                parent_query=self.parent_query,
                cost_callback=self.add_costs,
                headers=self.headers,
                prompt_family=self.prompt_family,
                **self.kwargs
            )
            await self._log_event(
                "action",
                action="agent_selected",
                details={
                    "agent": self.agent,
                    "role": self.role,
                },
            )

        await self._log_event(
            "research",
            step="conducting_research",
            details={
                "agent": self.agent,
                "role": self.role,
            },
        )
        self.context = await self.research_conductor.conduct_research()

        await self._log_event(
            "research",
            step="research_completed",
            details={"context_length": len(self.context)},
        )

        # Initialize structured research pipeline if needed and not disabled
        if (
            not self.disable_structured_research
            and self.research_config
            and self.research_config.get("enable_structured_research")
        ):
            await self._log_event("action", action="initialize_structured_research")
            from gpt_researcher.llm_provider import GenericLLMProvider

            llm_provider: GenericLLMProvider = GenericLLMProvider(self.cfg.smart_llm_provider)
            self.structured_pipeline = StructuredResearchPipeline(llm_provider, self.cfg)

        return [] if self.context is None else self.context

    async def _handle_deep_research(
        self,
        on_progress: Callable[[str], None] | None = None,
    ) -> list[str]:
        """Handle deep research execution and logging."""
        # Log deep research configuration
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
        return self.context

    async def write_report(
        self,
        existing_headers: list[str] | None = None,
        relevant_written_contents: list[str] | None = None,
        ext_context: list[dict[str, Any]] | None = None,
        custom_prompt: str = "",
    ) -> str:
        # Enable LLM visualization for report generation
        enable_llm_visualization()

        await self._log_event(
            "research",
            step="writing_report",
            details={
                "existing_headers": existing_headers,
                "context_source": "external" if ext_context else "internal",
                #                "structured_research_enabled": self.structured_pipeline is not None and not self.disable_structured_research,
            },
        )

        # Use structured research if available and enabled and not disabled
        if (
            not self.disable_structured_research
            and self.structured_pipeline
            and self.research_config
        ):
            try:
                await self._log_event("research", step="running_structured_research")

                # Run structured research pipeline
                results: ResearchResults = await self.structured_pipeline.run_structured_research(
                    topic=self.query,
                    sources=self.research_sources,
                    enable_debate=self.research_config.get("enable_debate", False),
                    min_confidence=self.research_config.get("min_confidence", 0.5),
                    max_sections=self.research_config.get("max_sections", 8),
                )

                # Export as markdown report
                report: str = self.structured_pipeline.export_results(results, format="markdown")

                await self._log_event(
                    "research",
                    step="structured_report_completed",
                    details={
                        "report_length": len(report),
                        "fact_count": results.fact_summary.get("total_facts", 0),
                        "sections": len(results.narrative.sections),
                        "overall_quality": results.narrative.overall_quality.value,
                    },
                )

                return report

            except Exception as e:
                await self._log_event(
                    "research",
                    step="structured_research_failed",
                    details={"error": f"{e.__class__.__name__}: {e}"},
                )
                # Fall back to regular report generation
                pass

        # Regular report generation
        report: str = await self.report_generator.write_report(
            existing_headers=existing_headers,
            relevant_written_contents=relevant_written_contents,
            ext_context=ext_context or self.context,
            custom_prompt=custom_prompt,
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
    ) -> list[dict[str, Any]]:
        # Use all retrievers as fallbacks
        return await get_search_results(
            query,
            self.retrievers[0],
            query_domains=query_domains,
            fallback_retrievers=self.retrievers[1:] if len(self.retrievers) > 1 else None,
            min_results=1,
        )

    async def get_subtopics(self) -> list[str]:
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
    def get_research_images(
        self,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        return self.research_images[:top_k]

    def add_research_images(
        self,
        images: list[dict[str, Any]],
    ) -> None:
        self.research_images.extend(images)

    def get_research_sources(self) -> list[dict[str, Any]]:
        return self.research_sources

    def add_research_sources(
        self,
        sources: list[dict[str, Any]],
    ) -> None:
        self.research_sources.extend(sources)

    def add_references(
        self,
        report_markdown: str,
        visited_urls: set,
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
        return [] if self.context is None else cast(list[str], self.context)

    def get_costs(self) -> float:
        return self.research_costs

    def set_verbose(
        self,
        verbose: bool,
    ) -> None:
        self.verbose = verbose

    def add_costs(
        self,
        cost: float,
    ) -> None:
        if not isinstance(cost, (float, int)):
            raise ValueError("Cost must be an integer or float")
        self.research_costs += cost
        if self.log_handler is not None:
            _: Coroutine[Any, Any, None] = self._log_event(
                "research",
                step="cost_update",
                details={
                    "cost": cost,
                    "total_cost": self.research_costs,
                },
            )
