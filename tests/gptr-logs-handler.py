from typing import Dict, Any
import asyncio
from gpt_researcher import GPTResearcher

class CustomLogsHandler:
    """A custom Logs handler class to handle JSON data."""
    def __init__(self):
        self.logs = []  # Initialize logs to store data

    async def send_json(self, data: Dict[str, Any]) -> None:
        """Send JSON data and log it."""
        self.logs.append(data)  # Append data to logs
        print(f"My custom Log: {data}")  # For demonstration, print the log

async def run():
    # Define the necessary parameters with sample values

    query = "What happened in the latest burning man floods?"
    report_type = "research_report"  # Type of report to generate
    report_source = "online"  # Could specify source like 'online', 'books', etc.
    tone = "informative"  # Tone of the report ('informative', 'casual', etc.)
    config_path = None  # Path to a config file, if needed

    # Initialize researcher with a custom WebSocket
    custom_logs_handler = CustomLogsHandler()

    researcher = GPTResearcher(
        query=query,
        report_type=report_type,
        report_source=report_source,
        tone=tone,
        config_path=config_path,
        websocket=custom_logs_handler
    )

    await researcher.conduct_research()  # Conduct the research
    report = await researcher.write_report()  # Write the research report

    return report

# Run the asynchronous function using asyncio
if __name__ == "__main__":
    asyncio.run(run())
