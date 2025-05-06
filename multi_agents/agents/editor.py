from __future__ import annotations

import asyncio

from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from langgraph.graph import END, StateGraph

from multi_agents.agents.researcher import ResearchAgent
from multi_agents.agents.reviewer import ReviewerAgent
from multi_agents.agents.reviser import ReviserAgent
from multi_agents.agents.utils.llms import call_model
from multi_agents.agents.utils.views import print_agent_output
from multi_agents.memory.draft import DraftState

if TYPE_CHECKING:
    from fastapi import WebSocket
    from langgraph.graph.state import CompiledStateGraph


class EditorAgent:
    """Agent responsible for editing and managing code."""

    def __init__(
        self,
        websocket: WebSocket | None = None,
        stream_output: Callable[[str, str, str, WebSocket | None], Coroutine[Any, Any, Any]] | None = None,
        headers: dict[str, Any] | None = None,
    ):
        self.websocket: WebSocket | None = websocket
        self.stream_output: Callable[[str, str, str, WebSocket | None], Coroutine[Any, Any, Any]] | None = stream_output
        self.headers: dict[str, Any] = {} if headers is None else headers

    async def plan_research(
        self,
        research_state: dict[str, Any],
    ) -> dict[str, Any]:
        """Plan the research outline based on initial research and task parameters.

        Args:
            research_state: Dictionary containing research state information

        Returns:
            Dictionary with title, date, and planned sections
        """
        initial_research: str = str(research_state.get("initial_research") or "")
        task: dict[str, Any] = research_state.get("task") or {}
        model: str = str(task.get("model", "gpt-4o") or "gpt-4o")
        include_human_feedback: bool = bool(task.get("include_human_feedback", False))
        human_feedback: str | None = research_state.get("human_feedback")
        max_sections: int = int(task.get("max_sections", 10) or 10)

        prompt: list[dict[str, str]] = self._create_planning_prompt(
            initial_research,
            include_human_feedback,
            human_feedback,
            max_sections,
        )

        print_agent_output("Planning an outline layout based on initial research...", agent="EDITOR")
        plan: dict[str, Any] = await call_model(
            prompt=prompt, model=model, response_format="json"
        )
        plan = plan if isinstance(plan, dict) else {}
        return {
            "title": str(plan.get("title", "") or ""),
            "date": str(plan.get("date", "") or ""),
            "sections": list(plan.get("sections", []) or []),
        }

    async def run_parallel_research(
        self,
        research_state: dict[str, Any],
    ) -> dict[str, list[dict[str, Any]]]:
        """Execute parallel research tasks for each section.

        Args:
            research_state: Dictionary containing research state information
        Returns:
            Dictionary with research results
        """
        _agents: dict[str, Any] = self._initialize_agents()
        workflow: StateGraph = self._create_workflow()
        chain: CompiledStateGraph = workflow.compile()

        queries: list[str] = research_state.get("sections") or []
        title: str = research_state.get("title") or ""

        self._log_parallel_research(queries)

        research_results: list[dict[str, Any]] = [
            (await chain.ainvoke(self._create_task_input(research_state, query, title)))["draft"]
            for query in queries
        ]

        return {
            "research_data": research_results,
        }

    def _create_planning_prompt(
        self,
        initial_research: str,
        include_human_feedback: bool,
        human_feedback: str | None,
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
                "content": self._format_planning_instructions(
                    initial_research,
                    include_human_feedback,
                    human_feedback,
                    max_sections,
                ),
            },
        ]

    def _format_planning_instructions(
        self,
        initial_research: str,
        include_human_feedback: bool,
        human_feedback: str | None,
        max_sections: int,
    ) -> str:
        """Format the instructions for research planning."""
        today: str = datetime.now().strftime("%d/%m/%Y")
        feedback_instruction: str = (
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
        from gpt_researcher.utils.enum import Tone
        return {
            "research": ResearchAgent(
                websocket=self.websocket,
                stream_output=self.stream_output,
                tone=Tone.Objective,
                headers=self.headers,
            ),
            "reviewer": ReviewerAgent(
                websocket=self.websocket,
                stream_output=self.stream_output,
                headers=self.headers,
            ),
            "reviser": ReviserAgent(
                websocket=self.websocket,
                stream_output=self.stream_output,
                headers=self.headers,
            ),
        }

    def _create_workflow(self) -> StateGraph:
        """Create the workflow for the research process."""
        agents: dict[str, Any] = self._initialize_agents()
        research_agent: ResearchAgent = agents["research"]
        reviewer_agent: ReviewerAgent = agents["reviewer"]
        reviser_agent: ReviserAgent = agents["reviser"]

        workflow: StateGraph = StateGraph(DraftState)

        workflow.add_node("researcher", research_agent.run_depth_research)
        workflow.add_node("reviewer", reviewer_agent.run)
        workflow.add_node("reviser", reviser_agent.run)

        workflow.set_entry_point("researcher")
        workflow.add_edge("researcher", "reviewer")
        workflow.add_edge("reviser", "reviewer")

        def check_review(
            draft: dict[str, Any],
        ) -> str:
            review: dict[str, Any] | None = draft.get("review")
            return "accept" if review is None else "revise"

        workflow.add_conditional_edges(
            "reviewer",
            check_review,
            {"accept": END, "revise": "reviser"},
        )

        return workflow

    def _log_parallel_research(
        self,
        queries: list[str],
    ) -> None:
        """Log the start of parallel research tasks."""
        if self.websocket and self.stream_output:
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
            "initial_research": research_state.get("initial_research"),
        }
