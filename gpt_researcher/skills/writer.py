from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any

import asyncio

from gpt_researcher.actions import (
    generate_draft_section_titles,
    generate_report,
    stream_output,
    write_conclusion,
    write_report_introduction,
)
from gpt_researcher.utils.llm import construct_subtopics
from gpt_researcher.skills.llm_visualizer import LLMInteractionVisualizer, get_llm_visualizer

if TYPE_CHECKING:
    from gpt_researcher.agent import GPTResearcher


class ReportGenerator:
    """Generates reports based on research data."""

    def __init__(self, researcher: GPTResearcher):
        self.researcher: GPTResearcher = researcher
        self.research_params: dict[str, Any] = {
            "query": self.researcher.query,
            "agent_role_prompt": (
                self.researcher.cfg.agent_role  # pyright: ignore[reportAttributeAccessIssue]
                or self.researcher.role
            ),
            "report_type": self.researcher.report_type,
            "report_source": self.researcher.report_source,
            "tone": self.researcher.tone,
            "websocket": self.researcher.websocket,
            "cfg": self.researcher.cfg,
            "headers": self.researcher.headers,
        }

    async def write_report(
        self,
        existing_headers: list[str] | None = None,
        relevant_written_contents: list[str] | None = None,
        ext_context: list[dict[str, Any]] | None = None,
        custom_prompt: str = "",
        use_rag: bool = True,
    ) -> str:
        """Write a report based on existing headers and relevant contents.

        Args:
            existing_headers (list): List of existing headers.
            relevant_written_contents (list): List of relevant written contents.
            ext_context (Optional): External context, if any.
            custom_prompt (str): Custom prompt, if any.
            use_rag (bool): Whether to use RAG-based generation for large contexts.

        Returns:
            str: The generated report.
        """
        # Start visualization for report generation
        visualizer: LLMInteractionVisualizer = get_llm_visualizer()
        if visualizer.is_enabled():
            visualizer.start_report_flow(self.researcher.query, str(self.researcher.report_type))

        existing_headers = [] if existing_headers is None else existing_headers
        relevant_written_contents = [] if relevant_written_contents is None else relevant_written_contents
        ext_context = None if ext_context is None else ext_context

        # send the selected images prior to writing report
        research_images: list[dict[str, Any]] | None = self.researcher.get_research_images()
        if research_images:
            # Extract just the URLs from the image objects to match what the frontend expects
            image_urls: list[str] = [img.get("url", "") for img in research_images if img.get("url")]
            await stream_output("images", "selected_images", json.dumps(image_urls), self.researcher.websocket, True, research_images)

        context: list[dict[str, Any]] = ext_context or self.researcher.context
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "writing_report",
                f"✍️ Writing report for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        # Check if we should use RAG-based generation
        rag_enabled: bool = getattr(self.researcher.cfg, 'enable_rag_report_generation', False)
        should_use_rag: bool = use_rag and rag_enabled and self._should_use_rag_generation(context)

        if should_use_rag:
            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "using_rag_generation",
                    "🧠 Using RAG-based generation for comprehensive report...",
                    self.researcher.websocket,
                )

            # Use the new RAG-based report generation
            from gpt_researcher.actions.report_generation import generate_report_with_rag

            report: str = await generate_report_with_rag(
                query=self.researcher.query,
                context=context,
                agent_role_prompt=(
                    self.researcher.cfg.agent_role  # pyright: ignore[reportAttributeAccessIssue]
                    or self.researcher.role
                ),
                report_type=self.researcher.report_type,
                tone=self.researcher.tone,
                report_source=self.researcher.report_source,
                websocket=self.researcher.websocket,
                cfg=self.researcher.cfg,
                memory=self.researcher.memory,  # Pass memory for RAG
                main_topic=getattr(self.researcher, 'parent_query', ''),
                existing_headers=existing_headers,
                relevant_written_contents=relevant_written_contents,
                cost_callback=self.researcher.add_costs,
                custom_prompt=custom_prompt,
                headers=self.researcher.headers,
                prompt_family=self.researcher.prompt_family,
            )
        else:
            # Use original method for smaller contexts
            report_params: dict[str, Any] = self.research_params.copy()
            report_params["context"] = context

            if self.researcher.report_type == "subtopic_report":
                report_params.update(
                    {
                        "main_topic": self.researcher.parent_query,
                        "existing_headers": existing_headers,
                        "relevant_written_contents": relevant_written_contents,
                        "cost_callback": self.researcher.add_costs,
                        "custom_prompt": custom_prompt,
                    }
                )
            else:
                report_params["cost_callback"] = self.researcher.add_costs

            report = await generate_report(**report_params, **self.researcher.kwargs)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "report_written",
                f"📝 Report written for '{self.researcher.query}' ({len(report)} characters)",
                self.researcher.websocket,
            )

        # Finish visualization and generate flow diagram
        if visualizer.is_enabled():
            mermaid_diagram: str | None = visualizer.finish_flow()

            # Stream the visual diagram to the frontend if websocket available
            if mermaid_diagram and self.researcher.websocket:
                await stream_output(
                    "logs",
                    "llm_flow_diagram",
                    f"🎨 LLM Interaction Flow:\n{mermaid_diagram}",
                    self.researcher.websocket,
                )

        return report

    def _should_use_rag_generation(
        self,
        context: list[dict[str, Any]],
    ) -> bool:
        """Determine if RAG-based generation should be used based on context size.

        Args:
            context: The research context

        Returns:
            bool: True if RAG should be used, False otherwise
        """
        if not context:
            return False

        # Calculate total context size
        total_chars: int = 0
        total_items: int = len(context)

        for item in context:
            if isinstance(item, dict):
                if 'raw_content' in item:
                    total_chars += len(str(item['raw_content']))
                elif 'content' in item:
                    total_chars += len(str(item['content']))
                else:
                    total_chars += len(str(item))
            else:
                total_chars += len(str(item))

        # Use RAG if:
        # 1. We have a lot of research items (>20)
        # 2. OR total content is large (>50k characters)
        # 3. OR we're doing a detailed report
        use_rag: bool = (
            total_items > 20 or
            total_chars > 50000 or
            self.researcher.report_type == "detailed_report"
        )

        if use_rag and self.researcher.verbose:
            asyncio.create_task(stream_output(
                "logs",
                "rag_decision",
                f"🔍 RAG enabled: {total_items} items, {total_chars:,} chars, type: {self.researcher.report_type}",
                self.researcher.websocket,
            ))

        return use_rag

    async def write_report_conclusion(
        self,
        report_content: str,
    ) -> str:
        """Write the conclusion for the report.

        Args:
            report_content (str): The content of the report.

        Returns:
            str: The generated conclusion.
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "writing_conclusion",
                f"✍️ Writing conclusion for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        conclusion: str = await write_conclusion(
            query=self.researcher.query,
            context=report_content,
            config=self.researcher.cfg,
            agent_role_prompt=(
                self.researcher.cfg.agent_role  # pyright: ignore[reportAttributeAccessIssue]
                or self.researcher.role
            ),
            cost_callback=self.researcher.add_costs,
            websocket=self.researcher.websocket,
            prompt_family=self.researcher.prompt_family,
            **self.researcher.kwargs
        )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "conclusion_written",
                f"📝 Conclusion written for '{self.researcher.query}'",
                self.researcher.websocket,
            )

        return conclusion

    async def write_introduction(self) -> str:
        """Write the introduction section of the report."""
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "writing_introduction",
                f"✍️ Writing introduction for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        introduction: str = await write_report_introduction(
            query=self.researcher.query,
            context=self.researcher.context,
            agent_role_prompt=(
                self.researcher.cfg.agent_role  # pyright: ignore[reportAttributeAccessIssue]
                or self.researcher.role
            ),
            config=self.researcher.cfg,
            websocket=self.researcher.websocket,
            cost_callback=self.researcher.add_costs,
            prompt_family=self.researcher.prompt_family,
            **self.researcher.kwargs
        )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "introduction_written",
                f"📝 Introduction written for '{self.researcher.query}'",
                self.researcher.websocket,
            )

        return introduction

    async def get_subtopics(self) -> list[str]:
        """Retrieve subtopics for the research."""
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "generating_subtopics",
                f"🌳 Generating subtopics for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        subtopics: list[str] = await construct_subtopics(
            task=self.researcher.query,
            data=self.researcher.context,
            config=self.researcher.cfg,
            subtopics=self.researcher.subtopics,
            prompt_family=self.researcher.prompt_family,
            **self.researcher.kwargs
        )

        if self.researcher.verbose:
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
        """Generate draft section titles for the report.

        Args:
            current_subtopic (str): The current subtopic.

        Returns:
            list[str]: The draft section titles.
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "generating_draft_sections",
                f"📑 Generating draft section titles for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        draft_section_titles: list[str] = await generate_draft_section_titles(
            query=self.researcher.query,
            current_subtopic=current_subtopic,
            context=self.researcher.context,
            role=(
                self.researcher.cfg.agent_role  # pyright: ignore[reportAttributeAccessIssue]
                or self.researcher.role
            ),
            websocket=self.researcher.websocket,
            config=self.researcher.cfg,
            cost_callback=self.researcher.add_costs,
            prompt_family=self.researcher.prompt_family,
            **self.researcher.kwargs
        )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "draft_sections_generated",
                f"🗂️ Draft section titles generated for '{self.researcher.query}'",
                self.researcher.websocket,
            )

        return draft_section_titles
