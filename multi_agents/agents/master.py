import os
import time
from concurrent.futures import ThreadPoolExecutor
from langgraph.graph import Graph, END

# Import agent classes
from . import \
    WriterAgent, \
    EditorAgent, \
    PublisherAgent, \
    ResearchAgent


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
        publisher_agent = PublisherAgent(self.output_dir)

        # Define a Langchain graph
        workflow = Graph()

        # Add nodes for each agent
        workflow.add_node("browser", research_agent.run_initial_research)
        workflow.add_node("planner", editor_agent.create_outline)
        workflow.add_node("researcher", research_agent.run_depth_research)
        workflow.add_node("writer", writer_agent.run) # consider this to be 'editor' instead, then followed by critique and reviser.
        workflow.add_node("publisher", publisher_agent.run)
        # Set up edges
        '''workflow.add_conditional_edges(start_key='critique',
                                       condition=lambda x: "accept" if x['critique'] is None else "revise",
                                       conditional_edge_mapping={"accept": "design", "revise": "write"})'''

        workflow.add_edge('browser', 'planner')
        workflow.add_edge('planner', 'researcher')
        workflow.add_edge('researcher', 'writer')
        workflow.add_edge('writer', 'publisher')

        # set up start and end nodes
        workflow.set_entry_point("browser")
        workflow.add_edge('publisher', END)

        # compile the graph
        chain = workflow.compile()

        # Execute the graph for each query in parallel
        #with ThreadPoolExecutor() as executor:
        #    parallel_results = list(executor.map(lambda q: chain.invoke({"query": q}), queries))
        result = await chain.ainvoke(self.task)

        return result
