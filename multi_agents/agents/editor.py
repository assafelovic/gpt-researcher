from datetime import datetime
from .utils.views import print_agent_output
from .utils.llms import call_model
from langgraph.graph import StateGraph, END
import asyncio
import json

from memory.draft import DraftState
from . import \
    ResearchAgent, \
    ReviewerAgent, \
    ReviserAgent


class EditorAgent:
    def __init__(self):
        pass

    def plan_research(self, research_state: dict):
        """
        Curate relevant sources for a query
        :param summary_report:
        :return:
        :param total_sub_headers:
        :return:
        """

        initial_research = research_state.get("initial_research")
        task = research_state.get("task")
        max_sections = task.get("max_sections")
        prompt = [{
            "role": "system",
            "content": "You are a research director. Your goal is to oversee the research project"
                       " from inception to completion.\n "
        }, {
            "role": "user",
            "content": f"Today's date is {datetime.now().strftime('%d/%m/%Y')}\n."
                       f"Research summary report: '{initial_research}'\n\n"
                       f"Your task is to generate an outline of sections headers for the research project"
                       f" based on the research summary report above.\n"
                       f"You must generate a maximum of {max_sections} section headers.\n"
                       f"You must focus ONLY on related research topics for subheaders and do NOT include introduction, conclusion and references.\n"
                       f"You must return nothing but a JSON with the fields 'title' (str) and "
                       f"'sections' (maximum {max_sections} section headers) with the following structure: "
                       f"'{{title: string research title, date: today's date, "
                       f"sections: ['section header 1', 'section header 2', 'section header 3' ...]}}.\n "
        }]

        print_agent_output(f"Planning an outline layout based on initial research...", agent="EDITOR")
        response = call_model(prompt=prompt, model=task.get("model"), response_format="json")
        plan = json.loads(response)

        return {
            "title": plan.get("title"),
            "date": plan.get("date"),
            "sections": plan.get("sections")
        }

    async def run_parallel_research(self, research_state: dict):
        research_agent = ResearchAgent()
        reviewer_agent = ReviewerAgent()
        reviser_agent = ReviserAgent()
        queries = research_state.get("sections")
        title = research_state.get("title")
        workflow = StateGraph(DraftState)

        workflow.add_node("researcher", research_agent.run_depth_research)
        workflow.add_node("reviewer", reviewer_agent.run)
        workflow.add_node("reviser", reviser_agent.run)

        # set up edges researcher->reviewer->reviser->reviewer...
        workflow.set_entry_point("researcher")
        workflow.add_edge('researcher', 'reviewer')
        workflow.add_edge('reviser', 'reviewer')
        workflow.add_conditional_edges('reviewer',
                                       (lambda draft: "accept" if draft['review'] is None else "revise"),
                                       {"accept": END, "revise": "reviser"})

        chain = workflow.compile()

        # Execute the graph for each query in parallel
        print_agent_output(f"Running the following research tasks in parallel: {queries}...", agent="EDITOR")
        final_drafts = [chain.ainvoke({"task": research_state.get("task"), "topic": query, "title": title})
                        for query in queries]
        research_results = [result['draft'] for result in await asyncio.gather(*final_drafts)]

        return {"research_data": research_results}
