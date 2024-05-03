from datetime import datetime
from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI
from .utils.views import print_agent_output
from langgraph.graph import StateGraph, END
import asyncio
import json

from memory.draft import DraftState
from . import \
    ResearchAgent, \
    ReviewerAgent, \
    ReviserAgent


class EditorAgent:
    def __init__(self, task: dict):
        self.task = task

    def create_outline(self, summary_report: str):
        """
        Curate relevant sources for a query
        :param summary_report:
        :return:
        :param total_sub_headers:
        :return:
        """
        max_sections = self.task.get("max_sections")
        prompt = [{
            "role": "system",
            "content": "You are a research director. Your goal is to oversee the research project"
                       " from inception to completion.\n "
        }, {
            "role": "user",
            "content": f"Today's date is {datetime.now().strftime('%d/%m/%Y')}\n."
                       f"Research summary report: '{summary_report}'\n\n"
                       f"Your task is to generate an outline of sections headers for the research project"
                       f" based on the research summary report above.\n"
                       f"You must generate a maximum of {max_sections} section headers.\n"
                       f"You must focus ONLY on related research topics for subheaders and do NOT include introduction, conclusion and references.\n"
                       f"You must return nothing but a JSON with the fields 'title' (str) and "
                       f"'sections' (maximum {max_sections} section headers) with the following structure: "
                       f"'{{title: string research title, date: today's date, "
                       f"sections: ['section header 1', 'section header 2', 'section header 3' ...]}}.\n "
        }]

        lc_messages = convert_openai_messages(prompt)
        optional_params = {
            "response_format": {"type": "json_object"}
        }
        response = ChatOpenAI(model=self.task.get("model"), max_retries=1, model_kwargs=optional_params).invoke(lc_messages).content
        return json.loads(response)

    async def run_parallel_research(self, research_state: dict):
        research_agent = ResearchAgent()
        reviewer_agent = ReviewerAgent()
        reviser_agent = ReviserAgent()
        queries = research_state.get("sections")
        title = research_state.get("title")
        workflow = StateGraph(DraftState)

        workflow.add_node("researcher", research_agent.run_depth_research)
        #workflow.add_node("reviewer", reviewer_agent.run)
        #workflow.add_node("reviser", reviser_agent.run)
        # Set up edges
        '''workflow.add_conditional_edges(start_key='review',
                                       condition=lambda x: "accept" if x['review'] is None else "revise",
                                       conditional_edge_mapping={"accept": END, "revise": "reviser"})'''

        # set up start and end nodes
        workflow.set_entry_point("researcher")
        workflow.add_edge('researcher', END)

        chain = workflow.compile()

        # Execute the graph for each query in parallel
        print_agent_output(f"Running the following research tasks in parallel: {queries}...", agent="EDITOR")
        final_drafts = [chain.ainvoke({"task": research_state.get("task"), "topic": query, "title": title})
                        for query in queries]
        research_results = [result['draft'] for result in await asyncio.gather(*final_drafts)]

        return {"research_data": research_results}

    def run(self, research_state: dict):
        initial_research = research_state.get("initial_research")
        print_agent_output(f"Planning an outline layout based on initial research...", agent="EDITOR")
        research_info = self.create_outline(initial_research)
        return {
            "title": research_info.get("title"),
            "date": research_info.get("date"),
            "sections": research_info.get("sections")
        }
