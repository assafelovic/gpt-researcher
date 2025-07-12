from __future__ import annotations

from typing import Any

from fastapi import WebSocket

from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import Tone


class DetailedReport:
    def __init__(
        self,
        query: str,
        report_type: str,
        report_source: str,
        source_urls: list[str] | None = None,
        document_urls: list[str] | None = None,
        query_domains: list[str] | None = None,
        config_path: str | None = None,
        tone: Tone | str = Tone.Objective,
        websocket: WebSocket | None = None,
        subtopics: list[dict[str, Any]] | None = None,
        headers: dict[str, Any] | None = None,
        complement_source_urls: bool = False,
        mcp_configs: dict[str, Any] | None = None,
        mcp_strategy: str | None = None,
    ):
        self.query: str = query
        self.report_type: str = report_type
        self.report_source: str = report_source
        self.source_urls: list[str] = [] if source_urls is None else source_urls
        self.document_urls: list[str] = [] if document_urls is None else document_urls
        self.query_domains: list[str] = [] if query_domains is None else query_domains
        self.config_path: str | None = config_path
        self.tone: Tone = (
            tone
            if isinstance(tone, Tone)
            else Tone.Objective
            if tone is None
            else Tone(tone)
        )
        self.websocket: WebSocket | None = websocket
        self.subtopics: list[dict[str, Any]] | None = subtopics
        self.headers: dict[str, Any] | None = {} if headers is None else headers
        self.complement_source_urls: bool = complement_source_urls

        self.gpt_researcher: GPTResearcher = GPTResearcher(
            query=self.query,
            query_domains=self.query_domains,
            report_type="research_report",
            report_source=self.report_source,
            source_urls=self.source_urls,
            document_urls=self.document_urls,
            config_path=self.config_path,
            tone=self.tone,
            websocket=self.websocket,
            headers=self.headers,
            complement_source_urls=self.complement_source_urls,
            mcp_configs=mcp_configs,
            mcp_strategy=mcp_strategy,
        )
        self.existing_headers: list[dict[str, Any]] = []
        self.global_context: list[str] = []
        self.global_written_sections: list[str] = []
        self.global_urls: set[str] = set() if self.source_urls is None else set(self.source_urls)

    async def run(self) -> str:
        print("DEBUG: Starting detailed report generation")
        await self._initial_research()
        print("DEBUG: Initial research completed")

        subtopics: list[dict[str, Any]] = await self._get_all_subtopics()
        print(f"DEBUG: Got {len(subtopics)} subtopics: {[s.get('task', 'NO TASK') for s in subtopics]}")

        report_introduction: str = await self.gpt_researcher.write_introduction()
        print(f"DEBUG: Introduction written, length: {len(report_introduction)}")

        _, report_body = await self._generate_subtopic_reports(subtopics)
        print(f"DEBUG: Subtopic reports generated, report_body length: {len(report_body)}")

        self.gpt_researcher.visited_urls.update(self.global_urls)
        report: str = await self._construct_detailed_report(report_introduction, report_body)
        print(f"DEBUG: Final report constructed, length: {len(report)}")
        return report

    async def _initial_research(self) -> None:
        await self.gpt_researcher.conduct_research()

        # Convert context to strings if it contains dictionaries
        if self.gpt_researcher.context:
            context_strings: list[str] = []
            for item in self.gpt_researcher.context:
                if isinstance(item, str):
                    context_strings.append(item)
                elif isinstance(item, dict) and "raw_content" in item:
                    # Extract content from dict if it has raw_content key
                    content: str = item["raw_content"]
                    if content and isinstance(content, str):
                        context_strings.append(content)
                else:
                    # Convert other types to string as fallback
                    context_strings.append(str(item))
            self.global_context = context_strings
        else:
            self.global_context = []

        self.global_urls = self.gpt_researcher.visited_urls

    async def _get_all_subtopics(self) -> list[dict[str, Any]]:
        subtopics_data: list[str] = await self.gpt_researcher.get_subtopics()

        all_subtopics: list[dict[str, Any]] = []
        if subtopics_data:
            for subtopic in subtopics_data:
                all_subtopics.append({"task": subtopic})
        else:
            print(f"WARNING! No subtopics generated for query: '''\n{self.query}\n'''")

        return all_subtopics

    async def _generate_subtopic_reports(
        self,
        subtopics: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], str]:
        subtopic_reports: list[dict[str, Any]] = []
        subtopics_report_body: str = ""

        print(f"DEBUG: Processing {len(subtopics)} subtopics")
        for i, subtopic in enumerate(subtopics):
            print(f"DEBUG: Processing subtopic {i + 1}/{len(subtopics)}: {subtopic.get('task', 'NO TASK')}")
            result: dict[str, Any] = await self._get_subtopic_report(subtopic)
            print(f"DEBUG: Subtopic {i + 1} result - report length: {len(result.get('report', ''))}")
            if result["report"]:
                subtopic_reports.append(result)
                subtopics_report_body += f"\n\n\n{result['report']}"
                print(f"DEBUG: Added subtopic {i + 1} to report body. Total body length: {len(subtopics_report_body)}")
            else:
                print(f"DEBUG: Subtopic {i + 1} had empty report!")

        print(f"DEBUG: Final report body length: {len(subtopics_report_body)}")
        return subtopic_reports, subtopics_report_body

    async def _get_subtopic_report(
        self,
        subtopic: dict[str, Any],
    ) -> dict[str, Any]:
        current_subtopic_task: str = subtopic.get("task")
        subtopic_assistant: GPTResearcher = GPTResearcher(
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
        )

        # Safely assign context, handling both strings and dictionaries
        if self.global_context:
            try:
                # Try to deduplicate if all items are strings
                if all(isinstance(item, str) for item in self.global_context):
                    subtopic_assistant.context = list(set(self.global_context))
                else:
                    # If there are dictionaries, just assign directly without deduplication
                    subtopic_assistant.context = self.global_context.copy()
            except Exception:
                # Fallback: just assign directly
                subtopic_assistant.context = self.global_context.copy()
        else:
            subtopic_assistant.context = []

        await subtopic_assistant.conduct_research()

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

        self.global_written_sections.extend(self.gpt_researcher.extract_sections(subtopic_report))
        # Ensure context contains only strings (hashable types) for set operation
        context_strings: list[str] = []
        for item in subtopic_assistant.context:
            if isinstance(item, str):
                context_strings.append(item)
            elif isinstance(item, dict) and "raw_content" in item:
                # Extract content from dict if it has raw_content key
                content: str = item["raw_content"]
                if content and isinstance(content, str):
                    context_strings.append(content)
            else:
                # Convert other types to string as fallback
                context_strings.append(str(item))
        self.global_context = list(set(context_strings))

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
        print(f"DEBUG: Constructing detailed report with report_body length: {len(report_body)}")
        toc: str = self.gpt_researcher.table_of_contents(report_body)
        print(f"DEBUG: TOC generated, length: {len(toc)}")

        print(f"DEBUG: About to call write_report_conclusion with report_body length: {len(report_body)}")

        # Fix: If report_body is empty (no subtopics generated), use introduction as context
        conclusion_context = report_body if report_body.strip() else introduction
        print(f"DEBUG: Using conclusion_context length: {len(conclusion_context)} (using {'report_body' if report_body.strip() else 'introduction'})")

        conclusion: str = await self.gpt_researcher.write_report_conclusion(conclusion_context)
        print(f"DEBUG: Conclusion generated, length: {len(conclusion)}")

        conclusion_with_references: str = self.gpt_researcher.add_references(
            conclusion,
            self.gpt_researcher.visited_urls,
        )
        report: str = f"{introduction}\n\n{toc}\n\n{report_body}\n\n{conclusion_with_references}"
        return report
