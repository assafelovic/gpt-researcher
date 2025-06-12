import logging
from typing import List, Dict, Any
import asyncio
from gpt_researcher import GPTResearcher
from backend.server.server_utils import CustomLogsHandler  # Update import

async def run() -> None:
    """Run the research process and generate a report."""
    query = "What happened in the latest burning man floods?"
    report_type = "research_report"
    report_source = "online"
    tone = "informative"
    config_path = None

    custom_logs_handler = CustomLogsHandler(None, query)  # Pass query parameter

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
