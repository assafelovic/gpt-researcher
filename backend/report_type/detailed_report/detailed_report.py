from __future__ import annotations

import logging

from typing import TYPE_CHECKING, Any, ClassVar

from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportSource, ReportType, Tone
from gpt_researcher.utils.schemas import Subtopics

if TYPE_CHECKING:
    import os

    from fastapi import WebSocket


class DetailedReporter:
    logger: ClassVar[logging.Logger] = logging.getLogger(__name__)

    def __init__(
        self,
        query: str,
        report_type: str | ReportType,
        report_source: str | ReportSource,
        source_urls: list[str] | None = None,
        document_urls: list[str] | None = None,
        config_path: os.PathLike | str | None = None,
        tone: str | Tone = "",
        websocket: WebSocket | None = None,
        subtopics: list[dict[str, Any]] | None = None,
        headers: dict[str, Any] | None = None,
        query_domains: list[str] | None = None,
    ):
        self.query: str = query
        self.report_type: ReportType = ReportType.__members__[report_type.lower().title()] if isinstance(report_type, str) else report_type
        self.report_source: ReportSource = ReportSource.__members__[report_source.lower().capitalize()] if isinstance(report_source, str) else report_source
        self.source_urls: list[str] = [] if source_urls is None else source_urls
        self.document_urls: list[str] = [] if document_urls is None else document_urls
        self.config_path: os.PathLike | str | None = config_path
        self.tone: Tone | None = Tone.__members__[tone.lower().capitalize()] if isinstance(tone, str) else tone
        self.websocket: WebSocket | None = websocket
        self.subtopics: list[dict[str, Any]] = [] if subtopics is None else subtopics
        self.headers: dict[str, Any] = {} if headers is None else headers
        self.query_domains: list[str] = [] if query_domains is None else query_domains

        self.gpt_researcher: GPTResearcher = GPTResearcher(
            query=self.query,
            config_path=self.config_path,
            report_type=self.report_type.value,
            report_source=self.report_source.value,
            source_urls=self.source_urls,
            document_urls=self.document_urls,
            tone=self.tone,
            websocket=self.websocket,
            headers=self.headers,
            query_domains=self.query_domains,
        )
        self.existing_headers: list[dict[str, Any]] = []
        self.global_context: list[str] = []
        self.global_written_sections: list[str] = []
        self.global_urls: set[str] = set(self.source_urls) if self.source_urls else set()

    async def run(self) -> str:
        await self._initial_research()
        subtopics: list[dict[str, Any]] = await self._get_all_subtopics()
        report_introduction = await self.gpt_researcher.write_introduction()
        _, report_body = await self._generate_subtopic_reports(subtopics)
        self.gpt_researcher.visited_urls.update(self.global_urls)
        report = await self._construct_detailed_report(report_introduction, report_body)
        return report

    async def _initial_research(self):
        await self.gpt_researcher.conduct_research()
        self.global_context = list(set(self.gpt_researcher.context))
        self.global_urls = set(self.gpt_researcher.visited_urls)

    async def _get_all_subtopics(self) -> list[dict[str, Any]]:
        subtopics_data: list[str] | Subtopics = await self.gpt_researcher.get_subtopics()

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
            report_type=ReportType.SubtopicReport.value,
            report_source=self.report_source.value,
            websocket=self.websocket,
            headers=self.headers,
            parent_query=self.query,
            subtopics=[repr(subtopic) if isinstance(subtopic, dict) else subtopic for subtopic in self.subtopics],
            visited_urls=self.global_urls,
            agent_role=self.gpt_researcher.agent,
            tone=self.tone if isinstance(self.tone, Tone) else Tone(self.tone),
            context=list(set(self.global_context)),
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

        return {"topic": subtopic, "report": subtopic_report}

    async def _construct_detailed_report(
        self,
        introduction: str,
        report_body: str,
    ) -> str:
        toc: str = self.gpt_researcher.table_of_contents(report_body)
        conclusion: str = await self.gpt_researcher.write_report_conclusion(report_body)
        conclusion_with_references: str = self.gpt_researcher.add_references(conclusion, self.gpt_researcher.visited_urls)
        report: str = f"{introduction}\n\n{toc}\n\n{report_body}\n\n{conclusion_with_references}"
        return report
