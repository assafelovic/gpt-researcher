from __future__ import annotations

import datetime
import os
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from langgraph.graph import END, StateGraph

from ..memory.research import ResearchState

# Import agent classes
from . import EditorAgent, HumanAgent, PublisherAgent, ResearchAgent, WriterAgent
from .utils.utils import sanitize_filename

# from langgraph.checkpoint.memory import MemorySaver
from .utils.views import print_agent_output

if TYPE_CHECKING:
    from fastapi import WebSocket

    from gpt_researcher.utils.enum import Tone


class ChiefEditorAgent:
    """Agent responsible for managing and coordinating editing tasks."""

    def __init__(
        self,
        task: dict,
        websocket: WebSocket | None = None,
        stream_output: Callable | None = None,
        tone: Tone | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.task: dict[str, Any] = task
        self.websocket: WebSocket | None = websocket
        self.stream_output: Callable | None = stream_output
        self.headers: dict[str, str] = headers or {}
        self.tone: Tone | None = tone
        self.task_id: int = self._generate_task_id()
        self.output_dir: str = self._create_output_directory()

    def _generate_task_id(self) -> int:
        # Currently time based, but can be any unique identifier
        return int(time.time())

    def _create_output_directory(self) -> str:
        output_dir: str = "./outputs/" + sanitize_filename(
            f"run_{self.task_id}_{self.task.get('query')[0:40]}"
        )

        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def _initialize_agents(self) -> dict[str, Any]:
        return {
            "writer": WriterAgent(self.websocket, self.stream_output, self.headers),
            "editor": EditorAgent(self.websocket, self.stream_output, self.tone, self.headers),
            "research": ResearchAgent(self.websocket, self.stream_output, self.tone, self.headers),
            "publisher": PublisherAgent(self.output_dir, self.websocket, self.stream_output, self.headers),
            "human": HumanAgent(self.websocket, self.stream_output, self.headers)
        }

    def _create_workflow(self, agents: dict[str, Any]):
        workflow = StateGraph(ResearchState)

        # Add nodes for each agent
        workflow.add_node("browser", agents["research"].run_initial_research)
        workflow.add_node("planner", agents["editor"].plan_research)
        workflow.add_node("researcher", agents["editor"].run_parallel_research)
        workflow.add_node("writer", agents["writer"].run)
        workflow.add_node("publisher", agents["publisher"].run)
        workflow.add_node("human", agents["human"].review_plan)

        # Add edges
        self._add_workflow_edges(workflow)

        return workflow

    def _add_workflow_edges(self, workflow):
        workflow.add_edge("browser", "planner")
        workflow.add_edge("planner", "human")
        workflow.add_edge("researcher", "writer")
        workflow.add_edge("writer", "publisher")
        workflow.set_entry_point("browser")
        workflow.add_edge("publisher", END)

        # Add human in the loop
        workflow.add_conditional_edges(
            "human",
            lambda review: "accept" if review["human_feedback"] is None else "revise",
            {"accept": "researcher", "revise": "planner"},
        )

    def init_research_team(self):
        """Initialize and create a workflow for the research team."""
        agents: dict[str, Any] = self._initialize_agents()
        return self._create_workflow(agents)

    async def _log_research_start(self):
        message: str = (
            f"Starting the research process for query '{self.task.get('query')}'..."
        )
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs", "starting_research", message, self.websocket
            )
        else:
            print_agent_output(message, "MASTER")

    async def run_research_task(self, task_id: int | None = None) -> dict[str, Any]:
        """Run a research task with the initialized research team.

        Args:
            task_id (optional): The ID of the task to run.

        Returns:
            The result of the research task.
        """
        research_team = self.init_research_team()
        chain = research_team.compile()

        await self._log_research_start()

        config: dict[str, dict[str, Any]] = {
            "configurable": {
                "thread_id": task_id,
                "thread_ts": datetime.datetime.utcnow(),
            }
        }

        result: dict[str, Any] = await chain.ainvoke(
            {"task": self.task},
            config=config,
        )
        return result
