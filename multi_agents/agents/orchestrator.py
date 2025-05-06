from __future__ import annotations

from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Coroutine, cast

from gpt_researcher.utils.enum import Tone
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from multi_agents.agents.utils.utils import sanitize_filename
from multi_agents.agents.utils.views import print_agent_output
from multi_agents.memory.research import ResearchState

if TYPE_CHECKING:
    from logging import Logger

    from fastapi import WebSocket
    from langchain_core.runnables.config import RunnableConfig
    from langgraph.graph.state import CompiledStateGraph

logger: Logger = getLogger(__name__)


class ChiefEditorAgent:
    """Agent responsible for managing and coordinating editing tasks."""

    def __init__(
        self,
        task: dict[str, Any],
        websocket: WebSocket | None = None,
        stream_output: Callable[[str, str, str, WebSocket | None], Coroutine[Any, Any, None]]
        | None = None,
        tone: Tone | str | None = None,
        headers: dict[str, Any] | None = None,
    ):
        self.task: dict[str, Any] = task
        self.websocket: WebSocket | None = websocket
        self.stream_output: (
            Callable[[str, str, str, WebSocket | None], Coroutine[Any, Any, None]] | None
        ) = stream_output
        self.headers: dict[str, Any] = {} if headers is None else headers
        self.tone: Tone = (
            Tone.__members__[tone.capitalize()]
            if isinstance(tone, str) and tone.capitalize() in Tone.__members__
            else tone
            if isinstance(tone, Tone)
            else Tone(tone)
            if isinstance(tone, str)
            else Tone.Objective
        )
        self.task_id: int = self._generate_task_id()
        self.output_dir: Path = self._create_output_directory()

    def _generate_task_id(self) -> int:
        """Generate a unique task ID."""
        # Currently time based, but can be any unique identifier
        return int(datetime.now(timezone.utc).timestamp())

    def _create_output_directory(self) -> Path:
        task_filename = sanitize_filename(f"run_{self.task_id}_{(self.task.get('query', {}) or {})[0:40]}")
        output_filepath = Path("./outputs/", task_filename)
        output_filepath.parent.mkdir(parents=True, exist_ok=True)
        return output_filepath

    def _initialize_agents(self) -> dict[str, Any]:
        from multi_agents.agents import (
            EditorAgent,
            HumanAgent,
            PublisherAgent,
            ResearchAgent,
            WriterAgent,
        )

        return {
            "writer": WriterAgent(self.websocket, self.stream_output, self.headers),
            "editor": EditorAgent(self.websocket, self.stream_output, self.headers),
            "research": ResearchAgent(self.websocket, self.stream_output, self.tone, self.headers),
            "publisher": PublisherAgent(self.output_dir.as_posix(), self.websocket, self.stream_output, self.headers),
            "human": HumanAgent(self.websocket, self.stream_output, self.headers),
        }

    def _create_workflow(
        self,
        agents: dict[str, Any],
    ) -> StateGraph:
        workflow = StateGraph(ResearchState)

        # Add nodes for each agent
        from multi_agents.agents.editor import EditorAgent
        from multi_agents.agents.human import HumanAgent
        from multi_agents.agents.publisher import PublisherAgent
        from multi_agents.agents.researcher import ResearchAgent
        from multi_agents.agents.writer import WriterAgent

        workflow.add_node("browser", cast(ResearchAgent, agents["research"]).run_initial_research)
        workflow.add_node("planner", cast(EditorAgent, agents["editor"]).plan_research)
        workflow.add_node("researcher", cast(EditorAgent, agents["editor"]).run_parallel_research)
        workflow.add_node("writer", cast(WriterAgent, agents["writer"]).run)
        workflow.add_node("publisher", cast(PublisherAgent, agents["publisher"]).run)
        workflow.add_node("human", cast(HumanAgent, agents["human"]).review_plan)

        # Add edges
        self._add_workflow_edges(workflow)

        return workflow

    def _add_workflow_edges(
        self,
        workflow: StateGraph,
    ):
        workflow.add_edge("browser", "planner")
        workflow.add_edge("planner", "human")
        workflow.add_edge("researcher", "writer")
        workflow.add_edge("writer", "publisher")
        workflow.set_entry_point("browser")
        workflow.add_edge("publisher", END)

        # Add human in the loop
        def human_feedback_condition(review: dict[str, Any]) -> str:
            return "accept" if review["human_feedback"] is None else "revise"

        workflow.add_conditional_edges(
            "human",
            human_feedback_condition,
            {
                "accept": "researcher",
                "revise": "planner",
            },
        )

    def init_research_team(self) -> StateGraph:
        """Initialize and create a workflow for the research team."""
        agents = self._initialize_agents()
        return self._create_workflow(agents)

    async def _log_research_start(self):
        message = f"Starting the research process for query '{self.task.get('query')}'..."
        if self.websocket is not None and self.stream_output is not None:
            await self.stream_output("logs", "starting_research", message, self.websocket)
        else:
            print_agent_output(message, "MASTER")

    async def run_research_task(
        self,
        task_id: int | None = None,
    ) -> str:
        """Run a research task with the initialized research team.

        Args:
            task_id (optional): The ID of the task to run.

        Returns:
            The result of the research task.
        """
        research_team: StateGraph = self.init_research_team()
        chain: CompiledStateGraph = research_team.compile()

        await self._log_research_start()

        config: RunnableConfig = {
            "configurable": {
                "thread_id": task_id,
                "thread_ts": datetime.now(timezone.utc),
            }
        }

        result: dict[str, Any] = await chain.ainvoke(
            {"task": self.task},
            config=config,
        )
        logger.info(
            "chain.ainvoke result: ",
            result,
            f"({result!r})",
        )
        return result.get("research_report", "")
