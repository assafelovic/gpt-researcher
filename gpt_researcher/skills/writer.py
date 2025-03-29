from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any

from gpt_researcher.actions import (
    generate_draft_section_titles,
    generate_report,
    stream_output,
    write_conclusion,
    write_report_introduction,
)
from gpt_researcher.utils.llm import construct_subtopics

if TYPE_CHECKING:
    from gpt_researcher import GPTResearcher
    from gpt_researcher.utils.validators import Subtopics


class ReportGenerator:
    """Generates reports based on research data."""

    def __init__(
        self,
        researcher: GPTResearcher,
    ):
        self.researcher: GPTResearcher = researcher
        self.research_params: dict[str, Any] = {
            "query": self.researcher.query,
            "agent_role_prompt": (self.researcher.cfg.AGENT_ROLE or "").strip(),
            "report_type": self.researcher.cfg.REPORT_TYPE,
            "report_source": self.researcher.cfg.REPORT_SOURCE,
            "tone": self.researcher.tone,
            "websocket": self.researcher.websocket,
            "cfg": self.researcher.cfg,
            "headers": self.researcher.headers,
        }

    async def write_report(
        self,
        existing_headers: list[dict[str, Any]] | None = None,
        relevant_written_contents: list[str] | None = None,
        ext_context: str | None = None,
        custom_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Write a report based on existing headers and relevant contents.

        Args:
        ----
            existing_headers (list[dict[str, Any]]): List of existing headers.
            relevant_written_contents (list[str]): List of relevant written contents.
            ext_context (str | None): External context, if any.

        Returns:
        -------
            (str): The generated report.
        """
        existing_headers = [] if existing_headers is None else existing_headers
        relevant_written_contents = [] if relevant_written_contents is None else relevant_written_contents
        ext_context = (
            " ".join(self.researcher.context)
            if ext_context is None or not ext_context.strip()
            else ext_context
        )

        # send the selected images prior to writing report
        research_images: list[dict[str, Any]] = self.researcher.get_research_images()
        if research_images:
            await stream_output(
                "images",
                "selected_images",
                json.dumps(research_images),
                self.researcher.websocket,
                True,
                metadata={"images": research_images},
            )

        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "writing_report",
                f"✍️ Writing report for '{self.researcher.query}' ✍️...",
                self.researcher.websocket,
            )

        report_params: dict[str, Any] = self.research_params.copy()
        report_params["context"] = ext_context
        report_params["custom_prompt"] = custom_prompt

        if self.researcher.report_type == "subtopic_report":
            report_params.update(
                {
                    "main_topic": self.researcher.parent_query,
                    "existing_headers": existing_headers,
                    "relevant_written_contents": relevant_written_contents,
                    "cost_callback": self.researcher.add_costs,
                }
            )
        else:
            report_params["cost_callback"] = self.researcher.add_costs

        report: str = await generate_report(**report_params)

        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "report_written",
                f"📝 Report written for '{self.researcher.query}'",
                self.researcher.websocket,
            )

        return report

    async def write_report_conclusion(
        self,
        report_content: str,
    ) -> str:
        """Write the conclusion for the report.

        Args:
        ----
            report_content (str): The content of the report.

        Returns:
        -------
            (str): The generated conclusion to the entire report.
        """
        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "writing_conclusion",
                f"✍️ Writing conclusion for '{self.researcher.query}'...",
                self.researcher.websocket,
                True,
                {"report_content": report_content},
            )

        conclusion: str = await write_conclusion(
            query=self.researcher.query,
            context=report_content,
            config=self.researcher.cfg,
            agent_role_prompt=(self.researcher.cfg.AGENT_ROLE or self.researcher.role or "").strip(),
            cost_callback=self.researcher.add_costs,
            websocket=self.researcher.websocket,
        )

        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "conclusion_written",
                f"📝 Conclusion written for '{self.researcher.query}'",
                self.researcher.websocket,
                True,
                {"report_content": report_content},
            )

        return conclusion

    async def write_introduction(self) -> str:
        """Write the introduction section of the report."""
        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "writing_introduction",
                f"✍️ Writing introduction for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        introduction: str = await write_report_introduction(
            query=self.researcher.query,
            context=" ".join(self.researcher.context),
            agent_role_prompt=(self.researcher.cfg.AGENT_ROLE or "").strip(),
            config=self.researcher.cfg,
            websocket=self.researcher.websocket,
            cost_callback=self.researcher.add_costs,
        )

        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "introduction_written",
                f"📝 Introduction written for '{self.researcher.query}' 📝",
                self.researcher.websocket,
            )

        return introduction

    async def get_subtopics(self) -> list[str] | Subtopics:
        """Retrieve subtopics for the research."""
        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "generating_subtopics",
                f"🌳 Generating subtopics for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        subtopics: list[str] | Subtopics = await construct_subtopics(
            task=self.researcher.query,
            data=" ".join(self.researcher.context),
            config=self.researcher.cfg,
            subtopics=self.researcher.subtopics,
        )

        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "subtopics_generated",
                f"📊 Subtopics generated for '{self.researcher.query}'",
                self.researcher.websocket,
            )

        return subtopics

    async def get_draft_section_titles(
        self,
        current_subtopic: str,
    ) -> list[str]:
        """Generate draft section titles for the report."""
        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "generating_draft_sections",
                f"📑 Generating draft section titles for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        draft_section_titles: list[str] = await generate_draft_section_titles(
            query=self.researcher.query,
            current_subtopic=current_subtopic,
            context=" ".join(self.researcher.context),
            role=(self.researcher.cfg.AGENT_ROLE or "").strip(),
            websocket=self.researcher.websocket,
            config=self.researcher.cfg,
            cost_callback=self.researcher.add_costs,
        )

        if self.researcher.cfg.VERBOSE:
            await stream_output(
                "logs",
                "draft_sections_generated",
                f"🗂️ Draft section titles generated for '{self.researcher.query}' 🗂️",
                self.researcher.websocket,
            )

        return draft_section_titles
