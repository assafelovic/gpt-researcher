from datetime import datetime
from typing import Dict, Optional, List

from multi_agents.agents.utils.views import print_agent_output
from multi_agents.agents.utils.llms import call_model


class EditorAgent:
    """Agent responsible for planning the research outline."""

    def __init__(self, websocket=None, stream_output=None, tone=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.tone = tone
        self.headers = headers or {}

    async def plan_research(self, research_state: Dict[str, any]) -> Dict[str, any]:
        initial_research = research_state.get("initial_research")
        task = research_state.get("task")
        include_human_feedback = task.get("include_human_feedback")
        human_feedback = research_state.get("human_feedback")
        max_sections = task.get("max_sections")

        prompt = self._create_planning_prompt(
            initial_research, include_human_feedback, human_feedback, max_sections
        )

        print_agent_output(
            "Planning an outline layout based on initial research...", agent="EDITOR"
        )
        plan = await call_model(
            prompt=prompt,
            model=task.get("model"),
            response_format="json",
        )

        return {
            "title": plan.get("title"),
            "date": plan.get("date"),
            "sections": plan.get("sections"),
        }

    def _create_planning_prompt(
        self,
        initial_research: str,
        include_human_feedback: bool,
        human_feedback: Optional[str],
        max_sections: int,
    ) -> List[Dict[str, str]]:
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
                    initial_research, include_human_feedback, human_feedback, max_sections
                ),
            },
        ]

    def _format_planning_instructions(
        self,
        initial_research: str,
        include_human_feedback: bool,
        human_feedback: Optional[str],
        max_sections: int,
    ) -> str:
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
