import os
import asyncio
import pytest
from unittest.mock import AsyncMock
from gpt_researcher.agent import GPTResearcher
from backend.server.server_utils import CustomLogsHandler
from typing import List, Dict, Any

# Define the report types to test
report_types = ["research_report", "subtopic_report"]

# Define a common query and sources for testing
query = "what is gpt-researcher"


@pytest.mark.asyncio
@pytest.mark.parametrize("report_type", report_types)
async def test_gpt_researcher(report_type):
    mock_websocket = AsyncMock()
    custom_logs_handler = CustomLogsHandler(mock_websocket, query)
    # Create an instance of GPTResearcher
    researcher = GPTResearcher(
        query=query,
        query_domains=["github.com"],
        report_type=report_type,
        websocket=custom_logs_handler,
    )

    # Conduct research and write the report
    await researcher.conduct_research()
    report = await researcher.write_report()

    print(researcher.visited_urls)
    print(report)

    # Check if the report contains part of the query
    assert "gpt-researcher" in report

    # test if at least one url starts with "github.com" as it was limited to this domain
    matching_urls = [
        url for url in researcher.visited_urls if url.startswith("https://github.com")
    ]
    assert len(matching_urls) > 0


if __name__ == "__main__":
    pytest.main()
