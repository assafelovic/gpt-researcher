import os
import time
from langgraph.graph import Graph, END
from .utils.views import print_agent_output

# Import agent classes
from . import \
    WriterAgent, \
    EditorAgent, \
    PublisherAgent, \
    ResearchAgent
    #ReviewerAgent, \
    #RevisorAgent


class MasterAgent:
    def __init__(self, task: dict):
        self.output_dir = f"./outputs/run_{int(time.time())}_{task.get('query')}"
        self.task = task
        os.makedirs(self.output_dir, exist_ok=True)

    async def run(self):
        # Initialize agents
        writer_agent = WriterAgent()
        editor_agent = EditorAgent(self.task)
        research_agent = ResearchAgent()
        publisher_agent = PublisherAgent(self.output_dir, self.task)

        # Define a Langchain graph
        workflow = Graph()

        # Add nodes for each agent
        workflow.add_node("browser", research_agent.run_initial_research)
        workflow.add_node("planner", editor_agent.create_outline)
        workflow.add_node("researcher", research_agent.run_depth_research)
        workflow.add_node("writer", writer_agent.run)
        workflow.add_node("publisher", publisher_agent.run)
        # Set up edges
        '''workflow.add_conditional_edges(start_key='review',
                                       condition=lambda x: "accept" if x['review'] is None else "revise",
                                       conditional_edge_mapping={"accept": "publisher", "revise": "reviser"})'''

        workflow.add_edge('browser', 'planner')
        workflow.add_edge('planner', 'researcher')
        workflow.add_edge('researcher', 'writer')
        workflow.add_edge('writer', 'publisher')

        # set up start and end nodes
        workflow.set_entry_point("browser")
        workflow.add_edge('publisher', END)

        # compile the graph
        chain = workflow.compile()

        print_agent_output(f"Starting the research process for query '{self.task.get('query')}'...", "MASTER")
        result = await chain.ainvoke(self.task)

        return result
