import asyncio
import datetime
import os
import time
from typing import Any, Dict, List, Optional

from autogen import ConversableAgent, GroupChat, GroupChatManager, UserProxyAgent

from multi_agents.agents.utils.views import print_agent_output
from multi_agents.agents.utils.utils import sanitize_filename
from .editor import EditorAgent
from multi_agents.agents.human import HumanAgent
from multi_agents.agents.publisher import PublisherAgent
from multi_agents.agents.researcher import ResearchAgent
from multi_agents.agents.reviewer import ReviewerAgent
from multi_agents.agents.reviser import ReviserAgent
from multi_agents.agents.writer import WriterAgent


class ChiefEditorAgent:
    """AG2-orchestrated agent responsible for managing and coordinating tasks."""

    def __init__(self, task: dict, websocket=None, stream_output=None, tone=None, headers=None):
        self.task = task
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}
        self.tone = tone
        self.task_id = self._generate_task_id()
        self.output_dir = self._create_output_directory()
        self.ag2_agents, self.manager = self._initialize_ag2_team()

    def _generate_task_id(self) -> int:
        return int(time.time())

    def _create_output_directory(self) -> str:
        output_dir = "./outputs/" + sanitize_filename(
            f"run_{self.task_id}_{self.task.get('query')[0:40]}"
        )
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def _llm_config(self) -> Dict[str, Any]:
        model_name = self.task.get("model") or "gpt-4o"
        return {
            "config_list": [
                {
                    "model": model_name,
                    "api_type": "openai",
                }
            ],
            "temperature": 0,
        }

    def _initialize_ag2_team(self):
        llm_config = self._llm_config()

        agents = {
            "chief_editor": ConversableAgent(
                name="ChiefEditor",
                system_message="You coordinate the multi-agent research workflow.",
                llm_config=llm_config,
            ),
            "editor": ConversableAgent(
                name="Editor",
                system_message="You plan the research outline from initial findings.",
                llm_config=llm_config,
            ),
            "researcher": ConversableAgent(
                name="Researcher",
                system_message="You perform initial and deep research tasks.",
                llm_config=llm_config,
            ),
            "reviewer": ConversableAgent(
                name="Reviewer",
                system_message="You review drafts against the given guidelines.",
                llm_config=llm_config,
            ),
            "reviser": ConversableAgent(
                name="Reviser",
                system_message="You revise drafts based on reviewer feedback.",
                llm_config=llm_config,
            ),
            "writer": ConversableAgent(
                name="Writer",
                system_message="You compile the final report from research drafts.",
                llm_config=llm_config,
            ),
            "publisher": ConversableAgent(
                name="Publisher",
                system_message="You publish the final report in the requested formats.",
                llm_config=llm_config,
            ),
            "human": UserProxyAgent(
                name="Human",
                system_message="You provide optional feedback on the research plan.",
                human_input_mode="ALWAYS"
                if self.task.get("include_human_feedback")
                else "NEVER",
                code_execution_config=False,
            ),
        }

        group_chat = GroupChat(
            agents=list(agents.values()),
            messages=[],
            max_round=1,
            speaker_selection_method="manual",
        )
        manager = GroupChatManager(groupchat=group_chat, llm_config=llm_config)
        return agents, manager

    def _chat(self, agent_key: str, message: str) -> None:
        agent = self.ag2_agents.get(agent_key)
        if not agent:
            return
        agent.send(message, self.manager, request_reply=False)

    async def _log(self, agent_key: str, message: str, stream_tag: str = "logs") -> None:
        self._chat(agent_key, message)
        if self.websocket and self.stream_output:
            await self.stream_output(stream_tag, agent_key, message, self.websocket)
        else:
            print_agent_output(message, agent="MASTER")

    def _initialize_agents(self) -> Dict[str, Any]:
        return {
            "writer": WriterAgent(self.websocket, self.stream_output, self.headers),
            "editor": EditorAgent(self.websocket, self.stream_output, self.tone, self.headers),
            "research": ResearchAgent(self.websocket, self.stream_output, self.tone, self.headers),
            "publisher": PublisherAgent(self.output_dir, self.websocket, self.stream_output, self.headers),
            "reviewer": ReviewerAgent(self.websocket, self.stream_output, self.headers),
            "reviser": ReviserAgent(self.websocket, self.stream_output, self.headers),
            "human": HumanAgent(self.websocket, self.stream_output, self.headers),
        }

    async def _run_section(self, agents: Dict[str, Any], topic: str, title: str) -> Any:
        await self._log("researcher", f"Running in depth research on topic: {topic}")
        draft_result = await agents["research"].run_depth_research(
            {"task": self.task, "topic": topic, "title": title}
        )

        draft_state: Dict[str, Any] = {
            "task": self.task,
            "draft": draft_result.get("draft"),
            "revision_notes": None,
        }

        max_revisions = int(self.task.get("max_revisions", 3))
        for _ in range(max_revisions):
            await self._log("reviewer", "Reviewing draft...")
            review_result = await agents["reviewer"].run(draft_state)
            review_notes = review_result.get("review")
            if review_notes is None:
                break

            await self._log("reviser", "Revising draft based on feedback...")
            revision = await agents["reviser"].run(
                {**draft_state, "review": review_notes}
            )
            draft_state.update(revision)

        return draft_state.get("draft")

    async def _run_parallel_research(
        self, agents: Dict[str, Any], sections: List[str], title: str
    ) -> List[Any]:
        tasks = [self._run_section(agents, topic, title) for topic in sections]
        return await asyncio.gather(*tasks)

    async def run_research_task(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        agents = self._initialize_agents()

        await self._log(
            "chief_editor",
            f"Starting the research process for query '{self.task.get('query')}'...",
        )

        initial_state = await agents["research"].run_initial_research({"task": self.task})
        await self._log("researcher", "Initial research complete.")

        plan_state = {**initial_state}
        plan = await agents["editor"].plan_research(plan_state)
        await self._log("editor", f"Planned sections: {plan.get('sections')}")

        human_feedback = await agents["human"].review_plan({**plan_state, **plan})
        if human_feedback.get("human_feedback"):
            await self._log("human", f"Human feedback: {human_feedback.get('human_feedback')}")
            plan_state = {**plan_state, **plan, **human_feedback}
            plan = await agents["editor"].plan_research(plan_state)
            await self._log("editor", f"Revised sections: {plan.get('sections')}")

        sections = plan.get("sections") or []
        title = plan.get("title")
        date = plan.get("date") or datetime.datetime.utcnow().strftime("%d/%m/%Y")

        research_data = await self._run_parallel_research(agents, sections, title)

        research_state = {
            "task": self.task,
            "title": title,
            "date": date,
            "sections": sections,
            "research_data": research_data,
        }

        await self._log("writer", "Writing final report...")
        writing = await agents["writer"].run(research_state)
        full_state = {**research_state, **writing}

        await self._log("publisher", "Publishing final report...")
        published = await agents["publisher"].run(full_state)
        await self._log("chief_editor", "Research task completed.")

        return {**full_state, **published}
