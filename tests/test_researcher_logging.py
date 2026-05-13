import pytest
from pathlib import Path
import sys
import logging
import json
from urllib.parse import unquote

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
    # Compute output base: researcher generates paths relative to CWD
    # (typically the project root when running pytest)
    outputs_base = Path.cwd().resolve()

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
        logger.info(f"Report type: {type(report).__name__}")

        # Basic report assertions
        assert isinstance(report, dict)
        assert "output" in report

        output = report["output"]
        assert {"pdf", "docx", "md", "json"}.issubset(output.keys())

        # Detailed artifact verification
        json_rel = unquote(output["json"])
        assert json_rel, "JSON output path must not be empty"
        json_path = outputs_base / json_rel
        assert json_path.exists(), f"Expected JSON log file was not created: {json_path}"

        with json_path.open() as f:
            data = json.load(f)

        assert "timestamp" in data
        assert "events" in data
        assert "content" in data
        assert isinstance(data["events"], list)
        assert isinstance(data["content"], dict)
        assert data["content"].get("query") is not None

        # The report artifacts should also exist on disk.
        for key in ("pdf", "docx", "md"):
            artifact_rel = unquote(output[key])
            assert artifact_rel, f"{key} path must not be empty"
            artifact_path = outputs_base / artifact_rel
            assert artifact_path.exists(), f"Expected artifact was not created: {artifact_path}"
            logger.info(f"- {artifact_path.name}")

        # Clean up generated artifacts so the test does not leave state behind.
        for key in ("pdf", "docx", "md", "json"):
            artifact_rel = unquote(output[key])
            if not artifact_rel:
                continue
            artifact_path = outputs_base / artifact_rel
            if artifact_path.exists():
                artifact_path.unlink()
                logger.info(f"Deleted artifact: {artifact_path}")
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure gpt_researcher is installed and in your PYTHONPATH")
        raise
    except Exception as e:
        logger.error(f"Error during research: {e}")
        raise

if __name__ == "__main__":
    pytest.main([__file__])
