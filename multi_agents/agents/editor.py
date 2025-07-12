from __future__ import annotations

import asyncio

from datetime import datetime
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional

from fastapi import WebSocket
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from multi_agents.agents import ResearchAgent, ReviewerAgent, ReviserAgent
from multi_agents.agents.utils.llms import call_model
from multi_agents.agents.utils.views import print_agent_output
from multi_agents.memory.draft import DraftState

if TYPE_CHECKING:
    from gpt_researcher.utils.enum import Tone


class EditorAgent:
    """Agent responsible for editing and managing code."""

    def __init__(
        self,
        websocket: WebSocket | None = None,
        stream_output: Callable[[str, str, str, WebSocket], Awaitable[None]] | None = None,
        tone: Tone | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.websocket: WebSocket | None = websocket
        self.stream_output: Callable[[str, str, str, WebSocket], Awaitable[None]] | None = stream_output
        self.tone: Tone | None = tone
        self.headers: dict[str, str] = headers or {}

    async def plan_research(self, research_state: dict[str, Any]) -> dict[str, Any]:
        """
        Plan the research outline based on initial research and task parameters.

        :param research_state: Dictionary containing research state information
        :return: Dictionary with title, date, and planned sections
        """
        initial_research = research_state.get("initial_research")
        task = research_state.get("task")
        include_human_feedback = task.get("include_human_feedback")
        human_feedback = research_state.get("human_feedback")
        max_sections = task.get("max_sections")

        prompt = self._create_planning_prompt(initial_research, include_human_feedback, human_feedback, max_sections)

        print_agent_output("Planning an outline layout based on initial research...", agent="EDITOR")
        plan = await call_model(
            prompt=prompt,
            model=task.get("model"),
            response_format="json",
        )

        return plan

    async def run_parallel_research(self, research_state: dict[str, Any]) -> dict[str, list[str]]:
        """Execute parallel research tasks for each section.

        Args:
            research_state: Dictionary containing research state information
            stream_output: Function to stream output to the client
            tone: Tone of the research
            headers: Headers for the research

        Returns:
            Dictionary with research results and research data
        """
        agents: dict[str, Any] = self._initialize_agents()
        workflow: StateGraph = self._create_workflow()
        chain: CompiledStateGraph = workflow.compile()

        queries: list[str] = research_state.get("sections")
        title: str = research_state.get("title")

        self._log_parallel_research(queries)

        final_drafts: list[Awaitable[dict[str, Any]]] = [chain.ainvoke(self._create_task_input(research_state, query, title)) for query in queries]
        research_results: list[dict[str, Any]] = [result["draft"] for result in await asyncio.gather(*final_drafts)]

        return {"research_data": research_results}

    def _create_planning_prompt(
        self,
        initial_research: str,
        include_human_feedback: bool,
        human_feedback: Optional[str],
        max_sections: int,
    ) -> list[dict[str, str]]:
        """Create the prompt for research planning."""
        return [
            {
                "role": "system",
                "content": "You are a research editor. Your goal is to oversee the research project "
                "from inception to completion. Your main task is to plan the article section "
                "layout based on an initial research summary.\n ",
            },
            {
                "role": "user",
                "content": self._format_planning_instructions(initial_research, include_human_feedback, human_feedback, max_sections),
            },
        ]

    def _format_planning_instructions(
        self,
        initial_research: str,
        include_human_feedback: bool,
        human_feedback: Optional[str],
        max_sections: int,
    ) -> str:
        """Format the instructions for research planning."""
        today = datetime.now().strftime("%d/%m/%Y")
        feedback_instruction = (
            f"Human feedback: {human_feedback}. You must plan the sections based on the human feedback."
            if include_human_feedback and human_feedback and human_feedback != "no"
            else ""
        )

        return f"""Today's date is {today}
                   Research summary report: '{initial_research}'
                   {feedback_instruction}
                   \nYour task is to generate an outline of sections headers for the research project
                   based on the research summary report above.
                   You must generate a maximum of {max_sections} section headers.
                   You must focus ONLY on related research topics for subheaders and do NOT include introduction, conclusion and references.
                   You must return nothing but a JSON with the fields 'title' (str) and
                   'sections' (maximum {max_sections} section headers) with the following structure:
                   '{{title: string research title, date: today's date,
                   sections: ['section header 1', 'section header 2', 'section header 3' ...]}}'."""

    def _initialize_agents(self) -> dict[str, Any]:
        """Initialize the research, reviewer, and reviser skills."""
        return {
            "research": ResearchAgent(self.websocket, self.stream_output, self.tone, self.headers),
            "reviewer": ReviewerAgent(self.websocket, self.stream_output, self.headers),
            "reviser": ReviserAgent(self.websocket, self.stream_output, self.headers),
        }

    def _create_workflow(self) -> StateGraph:
        """Create the workflow for the research process."""
        agents: dict[str, Any] = self._initialize_agents()
        workflow: StateGraph = StateGraph(DraftState)

        workflow.add_node("researcher", agents["research"].run_depth_research)
        workflow.add_node("reviewer", agents["reviewer"].run)
        workflow.add_node("reviser", agents["reviser"].run)

        workflow.set_entry_point("researcher")
        workflow.add_edge("researcher", "reviewer")
        workflow.add_edge("reviser", "reviewer")
        workflow.add_conditional_edges(
            "reviewer",
            lambda draft: "accept" if draft["review"] is None else "revise",
            {"accept": END, "revise": "reviser"},
        )

        return workflow

    def _log_parallel_research(self, queries: list[str]) -> None:
        """Log the start of parallel research tasks."""
        if self.websocket is not None and self.stream_output is not None:
            asyncio.create_task(
                self.stream_output(
                    "logs",
                    "parallel_research",
                    f"Running parallel research for the following queries: {queries}",
                    self.websocket,
                )
            )
        else:
            print_agent_output(
                f"Running the following research tasks in parallel: {queries}...",
                agent="EDITOR",
            )

    def _create_task_input(
        self,
        research_state: dict[str, Any],
        query: str,
        title: str,
    ) -> dict[str, Any]:
        """Create the input for a single research task."""
        return {
            "task": research_state.get("task"),
            "topic": query,
            "title": title,
            "headers": self.headers,
        }
