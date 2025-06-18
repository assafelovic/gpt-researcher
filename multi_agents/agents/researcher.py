from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, Callable

from colorama import Fore, Style
from fastapi import WebSocket
from gpt_researcher import GPTResearcher

from multi_agents.agents.utils.views import print_agent_output

if TYPE_CHECKING:
    from gpt_researcher.utils.enum import Tone

class ResearchAgent:
    def __init__(
        self,
        websocket: WebSocket | None = None,
        stream_output: Callable[[str, str, str, WebSocket], Awaitable[None]] | None = None,
        tone: Tone | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.websocket: WebSocket | None = websocket
        self.stream_output: Callable[[str, str, str, WebSocket], Awaitable[None]] | None = stream_output
        self.headers: dict[str, str] = {} if headers is None else headers
        self.tone: Tone | None = tone

    async def research(
        self,
        query: str,
        research_report: str = "research_report",
        parent_query: str = "",
        verbose: bool = True,
    ) -> str:
        # Initialize the researcher
        researcher: GPTResearcher = GPTResearcher(
            query=query,
            report_type=research_report,
            parent_query=parent_query,
            verbose=verbose,
            report_source=self.headers.get("report_source", "web"),
            tone=self.tone,
            websocket=self.websocket,
            headers=self.headers,
        )
        # Conduct research on the given query
        await researcher.conduct_research()
        # Write the report
        report = await researcher.write_report()

        return report

    async def run_subtopic_research(
        self,
        parent_query: str,
        subtopic: str,
        verbose: bool = True,
        source: str = "web",
    ) -> dict[str, Any]:
        try:
            report: dict[str, Any] = await self.research(
                parent_query=parent_query,
                query=subtopic,
                research_report="subtopic_report",
                verbose=verbose,
            )
        except Exception as e:
            print(f"{Fore.RED}Error in researching topic {subtopic}: {e}{Style.RESET_ALL}")
            report = None
        return {subtopic: report}

    async def run_initial_research(
        self,
        research_state: dict[str, Any],
    ) -> dict[str, Any]:
        task: dict[str, Any] = research_state.get("task")
        query: str = task.get("query")

        if self.websocket is not None and self.stream_output is not None:
            await self.stream_output("logs", "initial_research", f"Running initial research on the following query: {query}", self.websocket)
        else:
            print_agent_output(f"Running initial research on the following query: {query}", agent="RESEARCHER")
        return {
            "task": task,
            "initial_research": await self.research(
                query=query,
                verbose=task.get("verbose"),
            ),
        }

    async def run_depth_research(
        self,
        draft_state: dict[str, Any],
    ) -> dict[str, Any]:
        task: dict[str, Any] = draft_state.get("task")
        topic: str = draft_state.get("topic")
        parent_query: str = task.get("query")
        source: str = task.get("source", "web")
        verbose: bool = task.get("verbose")
        if self.websocket is not None and self.stream_output is not None:
            await self.stream_output(
                "logs",
                "depth_research",
                f"Running in depth research on the following report topic: {topic}",
                self.websocket,
            )
        else:
            print_agent_output(
                f"Running in depth research on the following report topic: {topic}",
                agent="RESEARCHER",
            )

        research_draft: dict[str, Any] = await self.run_subtopic_research(
            parent_query=parent_query,
            subtopic=topic,
            verbose=verbose,
            source=source,
        )
        return {"draft": research_draft}
