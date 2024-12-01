import asyncio
from langgraph.graph import StateGraph, END
from agents.Paser import ParserAgent
from agents.Solver import SolverAgent
from agents.Formatter import FormatterAgent
from agents.Explainer import ExplainerAgent
from agents.utils.views import print_agent_output
from multi_agents.memory.research import ResearchStateMath
import json
import os
from dotenv import load_dotenv

# Load environment variables
if os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
load_dotenv()

class MathWorkflow:
    """Workflow for solving and explaining math problems with formatting validation."""

    def __init__(self, task: dict, websocket=None, stream_output=None, headers=None):
        self.task = task
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}

    def _initialize_agents(self):
        """Initialize all agents used in the workflow."""
        return {
            "parser": ParserAgent(self.websocket, self.stream_output, self.headers),
            "solver": SolverAgent(self.websocket, self.stream_output, self.headers),
            "formatter": FormatterAgent(self.websocket, self.stream_output, self.headers),
            "explainer": ExplainerAgent(self.websocket, self.stream_output, self.headers),
        }

    def _create_workflow(self, agents):
        """Create the workflow using StateGraph."""
        workflow = StateGraph(ResearchStateMath)

        # Add nodes for each agent
        workflow.add_node("parser", agents["parser"].parse_problem)
        workflow.add_node("solver", agents["solver"].solve_problem)
        workflow.add_node("formatter", agents["formatter"].validate_solution)
        workflow.add_node("explainer", agents["explainer"].run)

        workflow.add_edge("parser", "solver")
        workflow.add_edge("solver", "formatter")

        # Routing function to decide the next node after formatter
        def routing(state, config):
            if state.get("validation_passed", False):
                return "explainer"
            return "solver"

        # Define edges and routing
        workflow.add_conditional_edges("formatter", routing)
        workflow.add_edge("explainer", END)
        # Set entry and finish point
        workflow.set_entry_point("parser")
        workflow.set_finish_point("explainer")  # Explicitly set "explainer" as the finish point
        return workflow

    async def run_workflow(self):
        """Run the entire workflow."""
        agents = self._initialize_agents()
        workflow = self._create_workflow(agents)

        # Compile the workflow to get the chain object
        chain = workflow.compile()

        # Define initial state with the problem description
        initial_state = {"task": self.task}

        # Run the workflow
        print_agent_output("Starting math problem workflow...", agent="MASTER")
        result = await chain.ainvoke(initial_state)
        print_agent_output("Workflow completed.", agent="MASTER")
        return result


# Main function to execute the workflow
async def main():
    # Define the math problem task
    task = {
        "problem": """○右の図はAB=3cm、BC=2cm、∠ABC=90°の
直角三角形ABCを底面とし、点D を頂点とする
三角錐であり、AD=6cm、∠ABD=∠CBD=90°である。
また、点Eは辺AD上の点で、AE=2cmである。
このとき、次の各問いに答えなさい。

①この三角錐の体積を求めなさい。""",
        "model": "gpt-4o",  # Model used for LLMs
        "verbose": True
    }

    # Initialize and run the workflow
    workflow = MathWorkflow(task=task)
    result = await workflow.run_workflow()
    # Print the result
    print("Final Result:", result)
    print(json.dumps(result, indent=4, ensure_ascii=False))



# Run the main function in an asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
