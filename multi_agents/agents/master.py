import os
import time
from langgraph.graph import StateGraph, END
from .utils.views import print_agent_output
from ..memory.research import ResearchState
from .utils.utils import sanitize_filename


# Import agent classes
from . import \
    WriterAgent, \
    EditorAgent, \
    PublisherAgent, \
    ResearchAgent

class ChiefEditorAgent:
    def __init__(self, task: dict, websocket=None, stream_output=None, tone=None, headers=None):
        self.task_id = int(time.time()) # Currently time based, but can be any unique identifier
        self.output_dir = "./outputs/" + sanitize_filename(f"run_{self.task_id}_{task.get('query')[0:40]}")
        self.task = task
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}
        self.tone = tone
        os.makedirs(self.output_dir, exist_ok=True)

    def init_research_team(self):
        # Initialize agents
        writer_agent = WriterAgent(self.websocket, self.stream_output, self.headers)
        editor_agent = EditorAgent(self.websocket, self.stream_output, self.headers)
        research_agent = ResearchAgent(self.websocket, self.stream_output, self.tone, self.headers)
        publisher_agent = PublisherAgent(self.output_dir, self.websocket, self.stream_output, self.headers)

        # Define a Langchain StateGraph with the ResearchState
        workflow = StateGraph(ResearchState)

        # Add nodes for each agent
        workflow.add_node("browser", research_agent.run_initial_research)
        workflow.add_node("planner", editor_agent.plan_research)
        workflow.add_node("researcher", editor_agent.run_parallel_research)
        workflow.add_node("writer", writer_agent.run)
        workflow.add_node("publisher", publisher_agent.run)

        workflow.add_edge('browser', 'planner')
        workflow.add_edge('planner', 'researcher')
        workflow.add_edge('researcher', 'writer')
        workflow.add_edge('writer', 'publisher')

        # set up start and end nodes
        workflow.set_entry_point("browser")
        workflow.add_edge('publisher', END)

        return workflow

    async def run_research_task(self):
        research_team = self.init_research_team()

        # compile the graph
        chain = research_team.compile()
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "starting_research", f"Starting the research process for query '{self.task.get('query')}'...", self.websocket)
        else:
            print_agent_output(f"Starting the research process for query '{self.task.get('query')}'...", "MASTER")
 
        result = await chain.ainvoke({"task": self.task})

        return result