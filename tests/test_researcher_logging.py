import pytest
import asyncio
from pathlib import Path
import sys
import logging

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_researcher_logging():  # Renamed function to be more specific
    """
    Test suite for verifying the researcher's logging infrastructure.
    Ensures proper creation and formatting of log files.
    """
    try:
        # Import here to catch any import errors
        from backend.server.server_utils import Researcher
        logger.info("Successfully imported Researcher class")
        
        # Create a researcher instance with a logging-focused query
        researcher = Researcher(
            query="Test query for logging verification",
            report_type="research_report"
        )
        logger.info("Created Researcher instance")
        
        # Run the research
        report = await researcher.research()
        logger.info("Research completed successfully!")
        logger.info(f"Report length: {len(report)}")
        
        # Basic report assertions
        assert report is not None
        assert len(report) > 0
        
        # Detailed log file verification
        logs_dir = Path(project_root) / "logs"
        log_files = list(logs_dir.glob("research_*.log"))
        json_files = list(logs_dir.glob("research_*.json"))
        
        # Verify log files exist
        assert len(log_files) > 0, "No log files were created"
        assert len(json_files) > 0, "No JSON files were created"
        
        # Log the findings
        logger.info(f"\nFound {len(log_files)} log files:")
        for log_file in log_files:
            logger.info(f"- {log_file.name}")
            # Could add additional checks for log file format/content here
            
        logger.info(f"\nFound {len(json_files)} JSON files:")
        for json_file in json_files:
            logger.info(f"- {json_file.name}")
            # Could add additional checks for JSON file structure here
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure gpt_researcher is installed and in your PYTHONPATH")
        raise
    except Exception as e:
        logger.error(f"Error during research: {e}")
        raise

if __name__ == "__main__":
    pytest.main([__file__]) 