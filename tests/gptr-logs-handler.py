import asyncio
import logging

from gpt_researcher import GPTResearcher
from backend.server.server_utils import CustomLogsHandler  # Update import


logger = logging.getLogger(__name__)


async def run() -> str:
    """Run the research process and generate a report."""
    query = "What happened in the latest burning man floods?"
    report_type = "research_report"
    report_source = "online"
    tone = "informative"
    # config_path = ...  # Path to the configuration file

    custom_logs_handler = CustomLogsHandler(
        task=query, websocket=None  # pyright: ignore[reportArgumentType]
    )  # Pass query parameter  # pyright: ignore[reportArgumentType]

    researcher = GPTResearcher(
        query=query,
        report_type=report_type,
        report_source=report_source,
        tone=tone,
        # config=config_path,
        websocket=custom_logs_handler,
    )

    await researcher.conduct_research()  # Conduct the research
    report = await researcher.write_report()  # Write the research report
    logger.info("Report generated successfully.")  # Log report generation

    return report


# Run the asynchronous function using asyncio
if __name__ == "__main__":
    asyncio.run(run())
