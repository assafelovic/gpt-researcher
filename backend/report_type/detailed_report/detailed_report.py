import asyncio
from typing import List, Dict, Set, Optional
from fastapi import WebSocket

from gpt_researcher.master.actions import (
    add_references,
    extract_headers,
    extract_sections,
    table_of_contents,
)
from gpt_researcher.master.agent import GPTResearcher
from gpt_researcher.utils.enum import Tone
from gpt_researcher.utils.validators import Subtopics
from gpt_researcher.master.actions.markdown_processing import extract_headers


class DetailedReport:
    def __init__(
        self,
        query: str,
        report_type: str,
        report_source: str,
        source_urls: List[str] = [],
        config_path: str = None,
        tone: Tone = Tone.Formal,
        websocket: WebSocket = None,
        subtopics: List[Dict] = [],
        headers: Optional[Dict] = None
    ):
        self.query = query
        self.report_type = report_type
        self.report_source = report_source
        self.source_urls = source_urls
        self.config_path = config_path
        self.tone = tone
        self.websocket = websocket
        self.subtopics = subtopics
        self.headers = headers or {}

        self.main_task_assistant = GPTResearcher(
            query=self.query,
            report_type="research_report",
            report_source=self.report_source,
            source_urls=self.source_urls,
            config_path=self.config_path,
            tone=self.tone,
            websocket=self.websocket,
            headers=self.headers
        )
        self.existing_headers: List[Dict] = []
        self.global_context: List[str] = []
        self.global_written_sections: List[str] = []
        self.global_urls: Set[str] = set(
            self.source_urls) if self.source_urls else set()

    async def run(self) -> str:
        await self._initial_research()
        subtopics = await self._get_all_subtopics()
        report_introduction = await self.main_task_assistant.write_introduction()
        _, report_body = await self._generate_subtopic_reports(subtopics)
        self.main_task_assistant.visited_urls.update(self.global_urls)
        report = await self._construct_detailed_report(report_introduction, report_body)
        return report

    async def _initial_research(self) -> None:
        await self.main_task_assistant.conduct_research()
        self.global_context = self.main_task_assistant.context
        self.global_urls = self.main_task_assistant.visited_urls

    async def _get_all_subtopics(self) -> List[Dict]:
        subtopics_data: Subtopics = await self.main_task_assistant.get_subtopics()

        all_subtopics = []
        if isinstance(subtopics_data, Subtopics):
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
        subtopic_assistant = GPTResearcher(
            query=current_subtopic_task,
            report_type="subtopic_report",
            report_source=self.report_source,
            websocket=self.websocket,
            headers=self.headers,
            parent_query=self.query,
            subtopics=self.subtopics,
            visited_urls=self.global_urls,
            agent=self.main_task_assistant.agent,
            role=self.main_task_assistant.role,
            tone=self.tone,
        )

        subtopic_assistant.context = list(set(self.global_context))
        await subtopic_assistant.conduct_research()

        draft_section_titles = await subtopic_assistant.get_draft_section_titles(current_subtopic_task)

        if not isinstance(draft_section_titles, str):
            draft_section_titles = str(draft_section_titles)

        parse_draft_section_titles = extract_headers(draft_section_titles)
        parse_draft_section_titles_text = [header.get(
            "text", "") for header in parse_draft_section_titles]

        relevant_contents = await subtopic_assistant.get_similar_written_contents_by_draft_section_titles(
            current_subtopic_task, parse_draft_section_titles_text, self.global_written_sections
        )

        subtopic_report = await subtopic_assistant.write_report(self.existing_headers, relevant_contents)

        self.global_written_sections.extend(extract_sections(subtopic_report))
        self.global_context = list(set(subtopic_assistant.context))
        self.global_urls.update(subtopic_assistant.visited_urls)

        self.existing_headers.append({
            "subtopic task": current_subtopic_task,
            "headers": extract_headers(subtopic_report),
        })

        return {"topic": subtopic, "report": subtopic_report}

    async def _construct_detailed_report(self, introduction: str, report_body: str) -> str:
        toc = table_of_contents(report_body)
        conclusion = await self.main_task_assistant.write_report_conclusion(report_body)
        conclusion_with_references = add_references(
            conclusion, self.main_task_assistant.visited_urls)
        report = f"{introduction}\n\n{toc}\n\n{report_body}\n\n{conclusion_with_references}"
        return report
