from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any

from gpt_researcher import GPTResearcher
from gpt_researcher.config.config import Config
from gpt_researcher.utils.enum import ReportFormat, ReportSource, ReportType, Tone
from gpt_researcher.utils.logger import get_formatted_logger
from gpt_researcher.utils.validators import Subtopics

if TYPE_CHECKING:
    import logging
    import os

    from fastapi import WebSocket

    from backend.server.server_utils import CustomLogsHandler



class DetailedReport:
    logger: logging.Logger = get_formatted_logger(__name__)

    def __init__(
        self,
        query: str,
        report_type: str | ReportType | None = None,
        report_source: str | ReportSource | None = None,
        websocket: WebSocket | CustomLogsHandler | None = None,
        report_format: str | ReportFormat | None = None,
        source_urls: list[str] | None = None,
        document_urls: list[str] | None = None,
        config_path: os.PathLike | str | None = None,
        tone: str | Tone | None = None,
        subtopics: list[dict[str, Any]] | None = None,
        headers: dict[str, Any] | None = None,
        query_domains: list[str] | None = None,
        config: Config | None = None,
        **kwargs: Any,
    ):
        self.cfg: Config = Config(config_path) if config is None else config
        for key, value in kwargs.items():
            self.cfg.__setattr__(key, value)
        self.document_urls: list[str] = [] if document_urls is None else document_urls
        self.existing_headers: list[dict[str, Any]] = kwargs.get("existing_headers", [])
        self.global_context: list[str] = kwargs.get("global_context", [])
        self.global_urls: set[str] = set(self.source_urls) if self.source_urls else set()
        self.global_written_sections: list[str] = kwargs.get("global_written_sections", [])
        self.headers: dict[str, Any] = {} if headers is None else headers
        self.query_domains: list[str] = [] if query_domains is None else query_domains
        self.query: str = query
        self.report_format: ReportFormat = (
            ReportFormat.__members__[report_format.lower().title()]
            if isinstance(report_format, str)
            else report_format
            if isinstance(report_format, ReportFormat)
            else ReportFormat.APA
        )
        self.report_source: ReportSource = (
            ReportSource.__members__[report_source.lower().capitalize()]
            if isinstance(report_source, str)
            else report_source
            if isinstance(report_source, ReportSource)
            else ReportSource.Web
        )
        self.report_type: ReportType = (
            ReportType.__members__[report_type.lower().title()]
            if isinstance(report_type, str)
            else report_type
            if isinstance(report_type, ReportType)
            else ReportType.ResearchReport
        )
        self.source_urls: list[str] = [] if source_urls is None else source_urls
        self.subtopics: list[dict[str, Any]] = [] if subtopics is None else subtopics
        self.tone: Tone | None = (
            Tone.__members__[tone.lower().capitalize()]
            if isinstance(tone, str)
            and tone.lower().capitalize() in Tone.__members__
            else tone
            if isinstance(tone, Tone)
            else Tone.Objective
        )
        self.websocket: WebSocket | CustomLogsHandler | None = websocket

        self.gpt_researcher: GPTResearcher = GPTResearcher(
            query=self.query,
            report_type=self.report_type,
            report_format=self.cfg.REPORT_FORMAT,
            report_source=self.report_source,
            tone=self.tone,
            source_urls=self.source_urls,
            document_urls=self.document_urls,
            config=self.cfg,
            websocket=self.websocket,
            headers=self.headers,
            query_domains=self.query_domains,
        )

    async def run(self) -> str:
        await self._initial_research()
        subtopics: list[dict[str, Any]] = await self._get_all_subtopics()
        report_introduction: str = await self.gpt_researcher.write_introduction()
        _, report_body = await self._generate_subtopic_reports(subtopics)
        self.gpt_researcher.visited_urls.update(self.global_urls)
        report: str = await self._construct_detailed_report(report_introduction, report_body)
        return report

    async def _initial_research(self):
        _research_result = await self.gpt_researcher.conduct_research()
        self.global_context = list(set(self.gpt_researcher.context))
        self.global_urls = set(self.gpt_researcher.visited_urls)

    async def _get_all_subtopics(self) -> list[dict[str, Any]]:
        subtopics_data: list[str] | Subtopics = await self.gpt_researcher.report_generator.get_subtopics()

        all_subtopics: list[dict[str, Any]] = []
        if isinstance(subtopics_data, Subtopics):
            for subtopic in subtopics_data.subtopics:
                all_subtopics.append({"task": subtopic.task})
        elif isinstance(subtopics_data, list):
            for subtopic in subtopics_data:
                all_subtopics.append({"task": subtopic})
        else:
            self.logger.warning(f"Unexpected subtopics data format: {subtopics_data}")
            return []

        return all_subtopics

    async def _generate_subtopic_reports(
        self,
        subtopics: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], str]:
        subtopic_reports: list[dict[str, Any]] = []
        subtopics_report_body: str = ""

        for subtopic in subtopics:
            result: dict[str, str] = await self._get_subtopic_report(subtopic)
            if result:
                subtopic_reports.append(result)
            report: str = str(result.get("report", "") or "").strip()
            if report:
                subtopics_report_body += f"\n\n\n{report}"

        return subtopic_reports, subtopics_report_body

    async def _get_subtopic_report(
        self,
        subtopic: dict[str, Any],
    ) -> dict[str, Any]:
        current_subtopic_task: str | None = subtopic.get("task", "")
        if current_subtopic_task is None:
            raise ValueError("Subtopic task is required")

        subtopic_assistant = GPTResearcher(
            query=current_subtopic_task,
            report_type=ReportType.SubtopicReport,
            report_format=self.cfg.REPORT_FORMAT,
            report_source=self.report_source,
            tone=self.tone,
            config=self.cfg,
            websocket=self.websocket,
            agent_role=self.gpt_researcher.role,
            parent_query=self.query,
            subtopics=[json.dumps(subtopic) for subtopic in self.subtopics],
            visited_urls=self.global_urls,
            context=list(set(self.global_context)),
            headers=self.headers,
            query_domains=self.query_domains,
        )

        _research_result: str | list[str] = await subtopic_assistant.conduct_research()
        draft_section_titles: str | list[str] = await subtopic_assistant.get_draft_section_titles(current_subtopic_task)

        if not isinstance(draft_section_titles, str):
            draft_section_titles = str(draft_section_titles)

        parse_draft_section_titles: list[dict[str, Any]] = self.gpt_researcher.extract_headers(draft_section_titles)
        parse_draft_section_titles_text: list[str] = [header.get("text", "") for header in parse_draft_section_titles]

        relevant_contents: list[str] = await subtopic_assistant.get_similar_written_contents_by_draft_section_titles(
            current_subtopic_task,
            parse_draft_section_titles_text,
            self.global_written_sections,
        )

        subtopic_report: str = await subtopic_assistant.write_report(
            self.existing_headers,
            relevant_contents,
        )

        self.global_written_sections.extend(
            [
                section.get("content", "")
                for section in self.gpt_researcher.extract_sections(subtopic_report)
            ]
        )
        self.global_context = list(set(subtopic_assistant.context))
        self.global_urls.update(subtopic_assistant.visited_urls)

        self.existing_headers.append(
            {
                "subtopic task": current_subtopic_task,
                "headers": self.gpt_researcher.extract_headers(subtopic_report),
            }
        )

        return {
            "report": subtopic_report,
            "research_result": _research_result,
            "subtopic task": current_subtopic_task,
            "topic": subtopic,
        }

    async def _construct_detailed_report(
        self,
        introduction: str,
        report_body: str,
    ) -> str:
        toc: str = self.gpt_researcher.table_of_contents(report_body)
        conclusion: str = await self.gpt_researcher.write_report_conclusion(report_body)
        urls: set[str] = {
            *list(self.global_urls),
            *self.document_urls,
            *self.gpt_researcher.visited_urls,
        }
        conclusion_with_references: str = self.gpt_researcher.add_references(conclusion, urls)
        report: str = f"{introduction}\n\n{toc}\n\n{report_body}\n\n{conclusion_with_references}"
        return report
