from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Awaitable, Callable

import json5 as json

from starlette.websockets import WebSocket

from multi_agents.agents.utils.llms import call_model
from multi_agents.agents.utils.views import print_agent_output

if TYPE_CHECKING:
    from fastapi import WebSocket

sample_json: str = """{
  "introduction": An indepth introduction to the topic in markdown syntax and hyperlink references to relevant sources,
  "conclusion": A conclusion to the entire research based on all research data in markdown syntax and hyperlink references to relevant sources,
  "sources": A list with strings of all used source links in the entire research data in markdown syntax and apa citation format. For example: ['-  Title, year, Author [source url](source)', ...]
}
"""


class WriterAgent:
    def __init__(
        self,
        websocket: WebSocket | None = None,
        stream_output: Callable[[str, str, str, WebSocket], Awaitable[None]] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.websocket: WebSocket | None = websocket
        self.stream_output: Callable[[str, str, str, WebSocket], Awaitable[None]] | None = stream_output
        self.headers: dict[str, str] = {} if headers is None else headers

    def get_headers(
        self,
        research_state: dict[str, Any],
    ) -> dict[str, str]:
        """Get the headers for the research report.

        Args:
            research_state (dict[str, Any]): The research state.

        Returns:
            dict[str, str]: The headers.
        """
        return {
            "title": research_state.get("title", ""),
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
        """Write the sections for the research report.

        Args:
            research_state (dict[str, Any]): The research state.

        Returns:
            dict[str, Any]: The research state.
        """
        query: str = research_state.get("title", "")
        data: str = research_state.get("research_data", "")
        task: dict[str, Any] = research_state.get("task", {})
        follow_guidelines: bool = task.get("follow_guidelines", False)
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
                f"Research data: {str(data)}\n"
                f"Your task is to write an in depth, well written and detailed "
                f"introduction and conclusion to the research report based on the provided research data. "
                f"Do not include headers in the results.\n"
                f"You MUST include any relevant sources to the introduction and conclusion as markdown hyperlinks -"
                f"For example: 'This is a sample text. ([url website](url))'\n\n"
                f"{f'You must follow the guidelines provided: {guidelines}' if follow_guidelines else ''}\n"
                f"You MUST return nothing but a JSON like the following:\n"
                f"{sample_json}\n\n"
                "Do NOT include any other text or comments, or backticks whatsoever. The entirety of your response must be completely 100% valid JSON containing the comprehensive and exhaustive report.",
            },
        ]

        response: dict[str, Any] = await call_model(
            prompt,
            task.get("model"),
            response_format="json",
        )
        if "table_of_contents" not in response:
            response["table_of_contents"] = ""
        return response

    async def revise_headers(
        self,
        task: dict[str, Any],
        headers: dict[str, Any],
    ) -> dict[str, Any]:
        """Revise the headers for the research report.

        Args:
            task (dict[str, Any]): The task.
            headers (dict[str, Any]): The headers.

        Returns:
            dict[str, Any]: The headers.
        """
        prompt: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": """
                You are a research writer.
Your sole Purpose is to revise the headers data based on the given guidelines.""",
            },
            {
                "role": "user",
                "content": f"""Your task is to revise the given headers JSON based on the guidelines given.
You are to follow the guidelines but the values should be in simple strings, ignoring all markdown syntax.
You must return nothing but a JSON in the same format as given in headers data.
Guidelines: {task.get("guidelines", "")}\n
Headers Data: {headers}\n
""",
            },
        ]

        response: dict[str, Any] = await call_model(
            prompt,
            task.get("model"),
            response_format="json",
        )
        return {"headers": response}

    async def run(
        self,
        research_state: dict[str, Any],
    ) -> dict[str, Any]:
        if self.websocket is not None and self.stream_output is not None:
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

        task_dict: dict[str, Any] = research_state.get("task", {})
        if task_dict.get("verbose"):
            if self.websocket is not None and self.stream_output is not None:
                research_layout_content_str: str = json.dumps(
                    research_layout_content,
                    indent=2,
                )
                await self.stream_output(
                    "logs",
                    "research_layout_content",
                    research_layout_content_str,
                    self.websocket,
                )
            else:
                print_agent_output(research_layout_content, agent="WRITER")

        headers: dict[str, str] = self.get_headers(research_state)
        if task_dict.get("follow_guidelines"):
            if self.websocket is not None and self.stream_output is not None:
                await self.stream_output(
                    "logs",
                    "rewriting_layout",
                    "Rewriting layout based on guidelines...",
                    self.websocket,
                )
            else:
                print_agent_output(
                    "Rewriting layout based on guidelines...",
                    agent="WRITER",
                )
            headers: dict[str, str] = await self.revise_headers(
                task=task_dict,
                headers=headers,
            )
            headers: dict[str, str] = headers.get("headers", {})

        return {**research_layout_content, "headers": headers}
