from .utils.views import print_agent_output
from .utils.llms import call_model

class VisualizerAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}

    async def generate_visualizations(self, research_state: dict):
        task = research_state.get("task")
        data = research_state.get("research_data", [])
        
        prompt = [
            {
                "role": "system",
                "content": "You are a Data Visualizer Agent. Your job is to extract key data points, processes, or timelines from the provided research data and generate a single relevant Mermaid.js diagram (such as a pie chart, flowchart, or timeline) to make the report more user-friendly.",
            },
            {
                "role": "user",
                "content": f"Research Data:\n{data}\n\nPlease generate a Mermaid diagram block representing the most interesting or structural aspect of this data. Ensure it uses standard markdown ```mermaid ... ``` syntax. If there is absolutely no suitable data for a diagram, return the exact string 'None'."
            }
        ]

        response = await call_model(prompt, model=task.get("model"))
        return response

    async def run(self, research_state: dict):
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "visualizing",
                f"Generating visualizations for the research report...",
                self.websocket,
            )
        else:
            print_agent_output(f"Generating visualizations for the research report...", agent="VISUALIZER")

        diagram_output = await self.generate_visualizations(research_state)

        diagrams = []
        if "None" not in diagram_output:
            diagrams.append(diagram_output)
            if self.websocket and self.stream_output:
                await self.stream_output("logs", "visualizing", f"Generated diagrams.", self.websocket)
            else:
                print_agent_output(f"Generated diagrams.", agent="VISUALIZER")
        else:
            if self.websocket and self.stream_output:
                await self.stream_output("logs", "visualizing", "No suitable data for visualizations.", self.websocket)
            else:
                print_agent_output("No suitable data for visualizations.", agent="VISUALIZER")

        return {"diagrams": diagrams}
