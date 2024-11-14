import os
import asyncio
import pytest
from gpt_researcher.agent import GPTResearcher
import logging
from typing import List, Dict, Any

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

# Define the report types to test
report_types = [
    "research_report",
    "subtopic_report"
]

# Define a common query and sources for testing
query = "What are the latest advancements in AI?"
# sources = ["https://en.wikipedia.org/wiki/Artificial_intelligence", "https://www.ibm.com/watson/ai"]

# Define the output directory
output_dir = "./outputs"

@pytest.mark.asyncio
@pytest.mark.parametrize("report_type", report_types)
async def test_gpt_researcher(report_type):
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    custom_logs_handler = CustomLogsHandler()
    # Create an instance of GPTResearcher
    researcher = GPTResearcher(query=query, report_type=report_type, websocket=custom_logs_handler)
    
    # Conduct research and write the report
    await researcher.conduct_research()
    report = await researcher.write_report()
    
    # Define the expected output filenames
    pdf_filename = os.path.join(output_dir, f"{report_type}.pdf")
    docx_filename = os.path.join(output_dir, f"{report_type}.docx")
    
    # Check if the PDF and DOCX files are created
    # assert os.path.exists(pdf_filename), f"PDF file not found for report type: {report_type}"
    # assert os.path.exists(docx_filename), f"DOCX file not found for report type: {report_type}"

    # Clean up the generated files (optional)
    # os.remove(pdf_filename)
    # os.remove(docx_filename)

if __name__ == "__main__":
    pytest.main()