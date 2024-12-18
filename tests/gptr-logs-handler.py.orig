import logging
from typing import List, Dict, Any
import asyncio
from gpt_researcher import GPTResearcher

class CustomLogsHandler:
    """A custom Logs handler class to handle JSON data."""
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []  # Initialize logs to store data
        logging.basicConfig(level=logging.INFO)  # Set up logging configuration

    async def send_json(self, data: Dict[str, Any]) -> None:
        """Send JSON data and log it, with error handling."""
        try:
            self.logs.append(data)  # Append data to logs
            logging.info(f"My custom Log: {data}")  # Use logging instead of print
        except Exception as e:
            logging.error(f"Error logging data: {e}")  # Log any errors

    def clear_logs(self) -> None:
        """Clear the logs."""
        self.logs.clear()  # Clear the logs list
        logging.info("Logs cleared.")  # Log the clearing action

async def run() -> None:
    """Run the research process and generate a report."""
    query = "What happened in the latest burning man floods?"
    report_type = "research_report"
    report_source = "online"
    tone = "informative"
    config_path = None

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
    logging.info("Report generated successfully.")  # Log report generation

    return report

# Run the asynchronous function using asyncio
if __name__ == "__main__":
    asyncio.run(run())
