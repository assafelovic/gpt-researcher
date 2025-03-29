from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

try:
    from gpt_researcher import GPTResearcher
except ImportError:
    import os
    import sys
    sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))  # Adjust the path to import GPTResearcher from the parent directory
    from gpt_researcher import GPTResearcher

from backend.server.server_utils import CustomLogsHandler  # Update import

OUTPUT_DIR = "./outputs"  # Define the output directory
REPORT_TYPES: list[str] = ["research_report", "subtopic_report"]  # Define the report types to test
QUERY = "what is gpt-researcher"  # Define a common query and sources for testing


@pytest.mark.asyncio
@pytest.mark.parametrize("report_type", REPORT_TYPES)
async def test_gpt_researcher(report_type: str) -> None:
    mock_websocket = AsyncMock()
    custom_logs_handler = CustomLogsHandler(mock_websocket, QUERY)
    # Create an instance of GPTResearcher
    researcher = GPTResearcher(
        query=QUERY,
        query_domains=["github.com"],
        report_type=report_type,
        websocket=custom_logs_handler,
    )

    # Conduct research and write the report
    _research_result: str | list[str] = await researcher.conduct_research()
    report: str = await researcher.write_report()

    print("--------------------------------")
    print(f"Report type: '{report_type}'")
    print(f"_research_result: '{_research_result}'")
    print(f"researcher.visited_urls: '{researcher.visited_urls}'")
    print(f"report: '{report}'")
    print("--------------------------------")

    # Check if the report contains part of the query
    assert "gpt-researcher" in report, "Report should contain 'gpt-researcher'"

    # test if at least one url starts with "github.com" as it was limited to this domain
    matching_urls: list[str] = [
        url
        for url in researcher.visited_urls
        if str(url).casefold().startswith("https://github.com")
    ]
    assert len(matching_urls) > 0, "At least one url should start with 'github.com'"


if __name__ == "__main__":
    pytest.main()
