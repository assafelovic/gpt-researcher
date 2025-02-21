from __future__ import annotations

import os

from logging import Logger, getLogger
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from gpt_researcher.utils.enum import ReportSource, Tone

from multi_agents.agents.utils.views import print_agent_output

if TYPE_CHECKING:
    from fastapi import WebSocket


logger: Logger = getLogger(__name__)


class ResearchAgent:
    def __init__(
        self,
        websocket: WebSocket | None = None,
        stream_output: Callable[[str, str, str, WebSocket | None], Coroutine[Any, Any, Any]] | None = None,
        tone: Tone | str | None = Tone.Objective,
        headers: dict[str, Any] | None = None,
    ):
        self.websocket: WebSocket | None = websocket
        self.stream_output: Callable[[str, str, str, WebSocket | None], Coroutine[Any, Any, Any]] | None = stream_output
        self.headers: dict[str, Any] = {} if headers is None else headers
        self.tone: Tone = Tone.Objective
        if isinstance(tone, str):
            self.tone = Tone.__members__[tone]
        elif isinstance(tone, Tone):
            self.tone = tone

    async def research(
        self,
        query: str,
        research_report: str = "research_report",
        parent_query: str = "",
        verbose: bool = True,
        source: ReportSource | str = ReportSource.Web,
        tone: Tone | str | None = Tone.Objective,
        headers: dict[str, Any] | None = None,
    ) -> str:
        if headers:
            self.headers.update(headers)

        from gpt_researcher.agent import GPTResearcher

        researcher = GPTResearcher(
            query=query,
            report_type=research_report,
            parent_query=parent_query,
            verbose=verbose,
            report_source=source.value if isinstance(source, ReportSource) else source,
            tone=tone.value if isinstance(tone, Tone) else tone,
            websocket=self.websocket,
            headers=self.headers,
        )
        await researcher.conduct_research()
        report: str = await researcher.write_report()
        logger.info(f"Research report: {report}")

        return report

    async def run_subtopic_research(
        self,
        parent_query: str,
        subtopic: str,
        verbose: bool = True,
        source: ReportSource | str = ReportSource.Web,
        headers: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        try:
            report: str = await self.research(
                parent_query=parent_query,
                query=subtopic,
                research_report="subtopic_report",
                verbose=verbose,
                source=source,
                tone=self.tone,
                headers=headers,
            )

        except Exception as e:
            logger.error(f"Error in researching topic {subtopic}: {e}")
            report = ""

        return {"subtopic": subtopic, "report": report}

    async def run_initial_research(
        self,
        research_state: dict[str, Any],
    ) -> dict[str, Any]:
        task: dict[str, Any] = research_state.get("task", {})
        query: str = task.get("query", "")
        source: ReportSource = task.get("source", ReportSource.Web)
        verbose: bool = task.get("verbose", True)

        if self.websocket is not None and self.stream_output is not None:
            await self.stream_output(
                "logs",
                "initial_research",
                f"Running initial research on the following query:{os.linesep * 2}```{os.linesep}{query}{os.linesep}```",
                self.websocket,
            )
        else:
            print_agent_output(
                f"Running initial research on the following query:{os.linesep * 2}```{os.linesep}{query}{os.linesep}```",
                agent="RESEARCHER",
            )
        return {
            "task": task,
            "initial_research": await self.research(
                query=query,
                verbose=verbose,
                source=source,
                tone=self.tone,
                headers=self.headers,
            ),
        }

    async def run_depth_research(
        self,
        draft_state: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        task: dict[str, Any] = draft_state.get("task", {})
        task = {} if task is None else task

        topic: str | None = draft_state.get("topic", "")
        topic = "" if topic is None else str(topic).strip()

        parent_query: str | None = task.get("query", "")
        parent_query = "" if parent_query is None else str(parent_query).strip()

        source: str | None = task.get("source", "web")
        report_source: ReportSource = ReportSource.Web if source is None else ReportSource.__members__[source.lower().capitalize()]

        v = task.get("verbose", True)
        verbose: bool = True if v is None else bool(v)

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
            source=report_source,
            headers=self.headers,
        )
        return {"draft": research_draft}
