from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from multi_agents.agents.utils.file_formats import write_md_to_pdf, write_md_to_word, write_text_to_md
from multi_agents.agents.utils.views import print_agent_output

if TYPE_CHECKING:
    import os

    from backend.server.server_utils import HTTPStreamAdapter
    from fastapi import WebSocket


class PublisherAgent:
    """Agent responsible for publishing the final research report."""

    def __init__(
        self,
        output_dir: os.PathLike | str,
        websocket: WebSocket | HTTPStreamAdapter | None = None,
        stream_output: Callable[[str, str, str, WebSocket | HTTPStreamAdapter | None], Coroutine[Any, Any, None]] | None = None,
        headers: dict[str, Any] | None = None,
    ):
        self.websocket: WebSocket | HTTPStreamAdapter | None = websocket
        self.stream_output: Callable[[str, str, str, WebSocket | HTTPStreamAdapter | None], Coroutine[Any, Any, None]] | None = stream_output
        self.output_dir: Path = Path(output_dir)
        self.headers: dict[str, Any] = {} if headers is None else headers

    async def publish_research_report(
        self,
        research_state: dict,
        publish_formats: dict,
    ):
        layout = self.generate_layout(research_state)
        await self.write_report_by_formats(layout, publish_formats)

        return layout

    def generate_layout(
        self,
        research_state: dict,
    ) -> str:
        sections: str = "\n\n".join(f"{value}" for subheader in research_state.get("research_data", []) for key, value in subheader.items())
        references: str = "\n".join(f"{reference}" for reference in research_state.get("sources", []) or [])
        headers: dict[str, Any] = research_state.get("headers", {})
        layout: str = f"""# {headers.get("title")}
#### {headers.get("date")}: {research_state.get("date")}

## {headers.get("introduction")}
{research_state.get("introduction")}

## {headers.get("table_of_contents")}
{research_state.get("table_of_contents")}

{sections}

## {headers.get("conclusion")}
{research_state.get("conclusion")}

## {headers.get("references")}
{references}
"""
        return layout

    async def write_report_by_formats(
        self,
        layout: str,
        publish_formats: dict,
    ):
        if publish_formats.get("pdf"):
            await write_md_to_pdf(layout, self.output_dir)
        if publish_formats.get("docx"):
            await write_md_to_word(layout, str(self.output_dir))
        if publish_formats.get("markdown"):
            await write_text_to_md(layout, self.output_dir)

    async def run(
        self,
        research_state: dict,
    ) -> dict[str, str]:
        task: dict[str, Any] = research_state.get("task", {})
        publish_formats: dict[str, Any] = task.get("publish_formats", {})
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "publishing",
                "Publishing final research report based on retrieved data...",
                self.websocket,
            )
        else:
            print_agent_output(
                output="Publishing final research report based on retrieved data...",
                agent="PUBLISHER",
            )
        final_research_report = await self.publish_research_report(research_state, publish_formats)
        return {"report": final_research_report}
