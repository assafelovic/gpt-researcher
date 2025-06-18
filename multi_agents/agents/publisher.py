from __future__ import annotations

import re

from typing import Any, Awaitable, Callable, Set

from fastapi import WebSocket

from multi_agents.agents.utils.file_formats import write_md_to_pdf, write_md_to_word, write_text_to_md
from multi_agents.agents.utils.utils import generate_slug
from multi_agents.agents.utils.views import print_agent_output


class PublisherAgent:
    def __init__(
        self,
        output_dir: str,
        websocket: WebSocket | None = None,
        stream_output: Callable[[str, str, str, WebSocket], Awaitable[None]] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.websocket: WebSocket | None = websocket
        self.stream_output: Callable[[str, str, str, WebSocket], Awaitable[None]] | None = stream_output
        self.output_dir: str = output_dir.strip()
        self.headers: dict[str, str] = {} if headers is None else headers

    async def publish_research_report(
        self,
        research_state: dict[str, Any],
        publish_formats: dict[str, Any],
    ) -> str:
        # layout: str = self.generate_layout(research_state)
        # Instead of calling generate_layout directly, we'll get the processed content and TOC
        processed_content, table_of_contents_md = self._generate_toc_and_process_content(research_state)

        layout: str = self._assemble_final_layout(research_state, processed_content, table_of_contents_md)
        await self.write_report_by_formats(layout, publish_formats)

        return layout

    def _generate_toc_and_process_content(
        self,
        research_state: dict[str, Any],
    ) -> tuple[str, str]:
        raw_sections_content: str = "\n\n".join(f"{value}" for subheader in research_state.get("research_data", []) for key, value in subheader.items())

        toc_entries: list[str] = []
        processed_lines: list[str] = []
        existing_slugs: Set[str] = set()
        header_pattern = re.compile(r"^(#{1,6})\s+(.+?)(?:\s*\{#(.*?)#\})?$")  # Supports existing slugs too

        for line in raw_sections_content.split("\n"):
            match = header_pattern.match(line)
            if match:
                header_level_md = match.group(1)  # e.g., ##
                header_text = match.group(2).strip()
                # existing_custom_slug = match.group(3) # Not used for now, always regenerating

                slug = generate_slug(header_text, existing_slugs)  # existing_slugs is passed by reference and updated

                indent_level = len(header_level_md) - 2  # Assuming H2 is base, H1 is not expected in sections
                indent = "  " * indent_level if indent_level > 0 else ""

                toc_entries.append(f"{indent}- [{header_text}](#{slug})")
                processed_lines.append(f"{header_level_md} {header_text} {{#{slug}}}")
            else:
                processed_lines.append(line)

        table_of_contents_md = "\n".join(toc_entries)
        processed_sections_content = "\n".join(processed_lines)

        return processed_sections_content, table_of_contents_md

    def _assemble_final_layout(
        self,
        research_state: dict[str, Any],
        processed_content: str,
        table_of_contents_md: str,
    ) -> str:
        references: str = "\n".join(f"{reference}" for reference in research_state.get("sources", []))
        headers: dict[str, Any] = research_state.get("headers", {})
        # The main report title itself won't be part of the auto-generated TOC
        # but we ensure it has an ID if we wanted to link to the very top.
        # For now, not adding a slug to the H1 title as TOC typically lists sections below H1.

        layout: str = f"""# {headers.get('title')}
#### {headers.get("date")}: {research_state.get('date')}

## {headers.get("introduction")}
{research_state.get('introduction')}

## {headers.get("table_of_contents")}
{table_of_contents_md}

{processed_content}

## {headers.get("conclusion")}
{research_state.get('conclusion')}

## {headers.get("references")}
{references}"""

        return layout

    async def write_report_by_formats(
        self,
        layout: str,
        publish_formats: dict[str, Any] | None = None,
    ) -> None:
        publish_formats = {} if publish_formats is None else publish_formats
        if publish_formats.get("pdf"):
            await write_md_to_pdf(layout, self.output_dir)
        if publish_formats.get("docx"):
            await write_md_to_word(layout, self.output_dir)
        if publish_formats.get("markdown"):
            await write_text_to_md(layout, self.output_dir)

    async def run(
        self,
        research_state: dict[str, Any],
    ) -> dict[str, Any]:
        task: dict[str, Any] = research_state.get("task")
        publish_formats: dict[str, Any] = task.get("publish_formats", {})
        if self.websocket is not None and self.stream_output is not None:
            await self.stream_output("logs", "publishing", "Publishing final research report based on retrieved data...", self.websocket)
        else:
            print_agent_output(output="Publishing final research report based on retrieved data...", agent="PUBLISHER")
        final_research_report: str = await self.publish_research_report(research_state, publish_formats)
        return {"report": final_research_report}
