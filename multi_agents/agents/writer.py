from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

import json5 as json

from multi_agents.agents.utils.llms import call_model
from multi_agents.agents.utils.views import print_agent_output

if TYPE_CHECKING:
    from fastapi import WebSocket

sample_json = """
{
    "table_of_contents": A table of contents in markdown syntax (using '-') based on the research headers and subheaders,
    "introduction": An indepth introduction to the topic in markdown syntax and hyperlink references to relevant sources,
    "conclusion": A conclusion to the entire research based on all research data in markdown syntax and hyperlink references to relevant sources,
    "sources": A list with strings of all used source links in the entire research data in markdown syntax and apa citation format. For example: ['-  Title, year, Author [source url](source)', ...]
}
"""


class WriterAgent:
    def __init__(
        self,
        websocket: WebSocket | None = None,
        stream_output: Any | None = None,
        headers: dict[str, Any] | None = None,
    ):
        self.websocket: WebSocket | None = websocket
        self.stream_output: Any | None = stream_output
        self.headers: dict[str, Any] | None = headers

    def get_headers(
        self,
        research_state: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "title": research_state.get("title"),
            "date": "Date",
            "introduction": "Introduction",
            "table_of_contents": "Table of Contents",
            "conclusion": "Conclusion",
            "references": "References",
        }

    async def write_sections(
        self,
        research_state: dict[str, Any],
    ) -> dict[str, Any]:
        query: str = research_state.get("title", "")
        data: str = research_state.get("research_data", "")

        task: dict[str, Any] = research_state.get("task", {})
        if not task:
            raise ValueError(f"Task is required, got {task!r}")
        if not isinstance(task, dict):
            raise ValueError(f"Task is in unexpected format, got {task!r}")
        follow_guidelines: bool = bool(task.get("follow_guidelines", False))
        guidelines: str = task.get("guidelines", "")

        prompt: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": "You are a research writer. Your sole purpose is to write a well-written "
                "research reports about a "
                "topic based on research findings and information.\n ",
            },
            {
                "role": "user",
                "content": f"Today's date is {datetime.now().strftime('%d/%m/%Y')}\n."
                f"Query or Topic: {query}\n"
                f"Research data: {data}\n"
                f"Your task is to write an in depth, well written and detailed "
                f"introduction and conclusion to the research report based on the provided research data. "
                f"Do not include headers in the results.\n"
                f"You MUST include any relevant sources to the introduction and conclusion as markdown hyperlinks -"
                f"For example: 'This is a sample text. ([url website](url))'\n\n"
                f"{f'You must follow the guidelines provided: {guidelines}' if follow_guidelines else ''}\n"
                f"You MUST return nothing but a JSON in the following format (without json markdown):\n"
                f"{sample_json}\n\n",
            },
        ]

        model: str = task.get("model", "")
        if not model:
            raise ValueError(f"Model is required, got {model!r}")
        if not isinstance(model, str):
            raise ValueError(f"Model is in unexpected format, got {model!r}")

        response: dict[str, Any] = await call_model(
            prompt,
            model,
            response_format="json",
        )

        return response

    async def revise_headers(
        self,
        task: dict[str, Any],
        headers: dict[str, Any],
    ) -> dict[str, Any]:
        prompt: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": """You are a research writer.
Your sole purpose is to revise the headers data based on the given guidelines.""",
            },
            {
                "role": "user",
                "content": f"""Your task is to revise the given headers JSON based on the guidelines given.
You are to follow the guidelines but the values should be in simple strings, ignoring all markdown syntax.
You must return nothing but a JSON in the same format as given in headers data.
Guidelines: {task["guidelines"]}\n
Headers Data: {headers}\n
""",
            },
        ]

        model: str = task.get("model", "")
        if not str(model).strip():
            raise ValueError(f"Model is required, got {model!r}")
        if not isinstance(model, str):
            raise ValueError(f"Model is in unexpected format, got {model!r}")

        response: dict[str, Any] = await call_model(
            prompt,
            model,
            response_format="json",
        )

        return response

    async def run(
        self,
        research_state: dict[str, Any],
    ) -> dict[str, Any]:
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "writing_report",
                "Writing final research report based on research data...",
                self.websocket,
            )
        else:
            print_agent_output(
                "Writing final research report based on research data...",
                agent="WRITER",
            )

        research_layout_content: dict[str, Any] = await self.write_sections(research_state)

        if not isinstance(research_layout_content, dict):
            raise ValueError(f"Research layout content is in unexpected format, got {research_layout_content!r}")
        task: dict[str, Any] = research_state.get("task", {})
        if not task:
            raise ValueError(f"Task is required, got {task!r}")
        if not isinstance(task, dict):
            raise ValueError(f"Task is in unexpected format, got {task!r}")

        if task.get("verbose"):
            if self.websocket and self.stream_output:
                research_layout_content_str = json.dumps(research_layout_content, indent=2)
                await self.stream_output(
                    "logs",
                    "research_layout_content",
                    research_layout_content_str,
                    self.websocket,
                )
            else:
                print_agent_output(json.dumps(research_layout_content, indent=2), agent="WRITER")

        headers: dict[str, Any] = self.get_headers(research_state)
        task: dict[str, Any] = research_state.get("task", None) or {}
        if not task:
            raise ValueError(f"Task is required, got {task!r}")
        if not isinstance(task, dict):
            raise ValueError(f"Task is in unexpected format, got {task!r}")
        if task.get("follow_guidelines"):
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "rewriting_layout",
                    "Rewriting layout based on guidelines...",
                    self.websocket,
                )
            else:
                print_agent_output("Rewriting layout based on guidelines...", agent="WRITER")
            task = research_state.get("task", {})
            if not task:
                raise ValueError(f"Task is required, got {task!r}")
            if not isinstance(task, dict):
                raise ValueError(f"Task is in unexpected format, got {task!r}")

            headers_response: dict[str, Any] = await self.revise_headers(task=task, headers=headers)
            headers = headers_response.get("headers", None) or {}

        return {**research_layout_content, "headers": headers}
