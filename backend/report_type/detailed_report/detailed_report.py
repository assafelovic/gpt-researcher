import asyncio
import logging
from typing import List, Dict, Set, Optional, Any
from fastapi import WebSocket

from gpt_researcher import GPTResearcher

logger = logging.getLogger(__name__)


class DetailedReport:
    def __init__(
        self,
        query: str,
        report_type: str,
        report_source: str,
        source_urls: List[str] = [],
        document_urls: List[str] = [],
        query_domains: List[str] = [],
        config_path: str = None,
        tone: Any = "",
        websocket: WebSocket = None,
        subtopics: List[Dict] = [],
        headers: Optional[Dict] = None,
        complement_source_urls: bool = False,
        mcp_configs=None,
        mcp_strategy=None,
    ):
        self.query = query
        self.report_type = report_type
        self.report_source = report_source
        self.source_urls = source_urls
        self.document_urls = document_urls
        self.query_domains = query_domains
        self.config_path = config_path
        self.tone = tone
        self.websocket = websocket
        self.subtopics = subtopics
        self.headers = headers or {}
        self.complement_source_urls = complement_source_urls
        
        # Initialize researcher with optional MCP parameters
        gpt_researcher_params = {
            "query": self.query,
            "query_domains": self.query_domains,
            "report_type": "research_report",
            "report_source": self.report_source,
            "source_urls": self.source_urls,
            "document_urls": self.document_urls,
            "config_path": self.config_path,
            "tone": self.tone,
            "websocket": self.websocket,
            "headers": self.headers,
            "complement_source_urls": self.complement_source_urls,
        }

        # Add MCP parameters if provided
        if mcp_configs is not None:
            gpt_researcher_params["mcp_configs"] = mcp_configs
        if mcp_strategy is not None:
            gpt_researcher_params["mcp_strategy"] = mcp_strategy

        self.gpt_researcher = GPTResearcher(**gpt_researcher_params)
        self.existing_headers: List[Dict] = []
        self.global_context: List[str] = []
        self.global_written_sections: List[str] = []
        self.global_urls: Set[str] = set(
            self.source_urls) if self.source_urls else set()

    async def run(self) -> str:
        await self._initial_research()
        subtopics = await self._get_all_subtopics()
        report_introduction = await self.gpt_researcher.write_introduction()
        _, report_body = await self._generate_subtopic_reports(subtopics)
        self.gpt_researcher.visited_urls.update(self.global_urls)
        report = await self._construct_detailed_report(report_introduction, report_body)
        return report

    async def _initial_research(self) -> None:
        await self.gpt_researcher.conduct_research()
        self.global_context = self.gpt_researcher.context
        self.global_urls = self.gpt_researcher.visited_urls

    async def _get_all_subtopics(self) -> List[Dict]:
        subtopics_data = await self.gpt_researcher.get_subtopics()

        all_subtopics = []
        if subtopics_data and subtopics_data.subtopics:
            for subtopic in subtopics_data.subtopics:
                all_subtopics.append({"task": subtopic.task})
        else:
            print(f"Unexpected subtopics data format: {subtopics_data}")

        return all_subtopics

    async def _generate_subtopic_reports(self, subtopics: List[Dict]) -> tuple:
        subtopic_reports = []
        subtopics_report_body = ""

        for subtopic in subtopics:
            result = await self._get_subtopic_report(subtopic)
            if result["report"]:
                subtopic_reports.append(result)
                subtopics_report_body += f"\n\n\n{result['report']}"

        return subtopic_reports, subtopics_report_body

    async def _get_subtopic_report(self, subtopic: Dict) -> Dict[str, str]:
        current_subtopic_task = subtopic.get("task")

        try:
            subtopic_assistant = GPTResearcher(
                query=current_subtopic_task,
                query_domains=self.query_domains,
                report_type="subtopic_report",
                report_source=self.report_source,
                websocket=self.websocket,
                headers=self.headers,
                parent_query=self.query,
                subtopics=self.subtopics,
                visited_urls=self.global_urls,
                agent=self.gpt_researcher.agent,
                role=self.gpt_researcher.role,
                tone=self.tone,
                complement_source_urls=self.complement_source_urls,
                source_urls=self.source_urls,
                # Propagate MCP configuration so follow-up researchers can use MCP
                mcp_configs=self.gpt_researcher.mcp_configs,
                mcp_strategy=self.gpt_researcher.mcp_strategy
            )

            subtopic_assistant.context = list(set(self.global_context))

            # Add timeout for research (3 minutes)
            try:
                await asyncio.wait_for(
                    subtopic_assistant.conduct_research(),
                    timeout=180.0  # 3 minutes timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Subtopic research timed out after 3 minutes: {current_subtopic_task}")
                # Return empty report for timed out subtopic
                return {"topic": subtopic, "report": f"# {current_subtopic_task}\n\n*Research timed out after 3 minutes*"}

            # Add timeout for draft section titles (1 minute)
            try:
                draft_section_titles = await asyncio.wait_for(
                    subtopic_assistant.get_draft_section_titles(current_subtopic_task),
                    timeout=60.0  # 1 minute timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Draft section titles extraction timed out for subtopic: {current_subtopic_task}")
                draft_section_titles = ""

            if not isinstance(draft_section_titles, str):
                draft_section_titles = str(draft_section_titles)

            parse_draft_section_titles = self.gpt_researcher.extract_headers(draft_section_titles)
            parse_draft_section_titles_text = [header.get(
                "text", "") for header in parse_draft_section_titles]

            # Add timeout for relevant contents (1 minute)
            try:
                relevant_contents = await asyncio.wait_for(
                    subtopic_assistant.get_similar_written_contents_by_draft_section_titles(
                        current_subtopic_task, parse_draft_section_titles_text, self.global_written_sections
                    ),
                    timeout=60.0  # 1 minute timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Relevant contents retrieval timed out for subtopic: {current_subtopic_task}")
                relevant_contents = []

            # Add timeout for report writing (5 minutes)
            try:
                subtopic_report = await asyncio.wait_for(
                    subtopic_assistant.write_report(self.existing_headers, relevant_contents),
                    timeout=300.0  # 5 minutes timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Report writing timed out for subtopic: {current_subtopic_task}")
                subtopic_report = f"# {current_subtopic_task}\n\n*Report generation timed out after 5 minutes*"

            self.global_written_sections.extend(self.gpt_researcher.extract_sections(subtopic_report))
            self.global_context = list(set(subtopic_assistant.context))
            self.global_urls.update(subtopic_assistant.visited_urls)

            self.existing_headers.append({
                "subtopic task": current_subtopic_task,
                "headers": self.gpt_researcher.extract_headers(subtopic_report),
            })

            return {"topic": subtopic, "report": subtopic_report}

        except Exception as e:
            logger.error(f"Error generating subtopic report for {current_subtopic_task}: {e}")
            return {"topic": subtopic, "report": f"# {current_subtopic_task}\n\n*Error: {str(e)}*"}

    async def _construct_detailed_report(self, introduction: str, report_body: str) -> str:
        toc = self.gpt_researcher.table_of_contents(report_body)
        conclusion = await self.gpt_researcher.write_report_conclusion(report_body)
        conclusion_with_references = self.gpt_researcher.add_references(
            conclusion, self.gpt_researcher.visited_urls)
        report = f"{introduction}\n\n{toc}\n\n{report_body}\n\n{conclusion_with_references}"
        return report
