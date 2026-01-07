import asyncio
from unittest.mock import MagicMock, AsyncMock
import sys
import os
from unittest.mock import MagicMock

# Mock fastapi
sys.modules["fastapi"] = MagicMock()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.report_type.detailed_report.detailed_report import DetailedReport

async def test_no_references():
    print("Setting up mock GPTResearcher...")
    
    # Mock GPTResearcher
    mock_researcher = MagicMock()
    mock_researcher.visited_urls = set()
    mock_researcher.write_research_gap = AsyncMock(return_value="## Research Gap")
    mock_researcher.write_introduction = AsyncMock(return_value="# Introduction")
    mock_researcher.write_report_conclusion = AsyncMock(return_value="## Conclusion")
    mock_researcher.add_references = MagicMock(return_value="## Conclusion\nREFERENCES")
    mock_researcher.table_of_contents = MagicMock(return_value="## TOC")
    
    class TestDetailedReport(DetailedReport):
        def __init__(self, researcher_mock):
            self.gpt_researcher = researcher_mock
            self.query = "test query"
            self.report_type = "detailed_report"
            self.report_source = "web"
            self.global_urls = set()
            self.global_context = []
            self.subtopics = []
            self.headers = {}
            
        async def _initial_research(self): pass
        async def _get_all_subtopics(self): return []
        async def _collect_subtopics_and_headers(self, subtopics):
            return [{"task": "Subtopic 1", "headers": [{"text": "Header 1"}]}]
        async def _reorganize_subtopics_and_headers(self, subtopics, headers=None):
             return [{"task": "Subtopic 1", "headers": [{"text": "Header 1"}]}]
        async def _generate_subtopic_reports(self, subtopics):
             return [], "## Subtopic 1"

    print("Running DetailedReport...")
    detailed_report = TestDetailedReport(mock_researcher)
    report = await detailed_report.run()
    
    print("\n--- Verification Results ---")
    
    # Verify add_references NOT called (or result ignored)
    # The code commented out the call, so add_references might not be called at all.
    # OR if it was called (but not used), verify logic.
    # The requirement is "Remove references from report". 
    
    if "REFERENCES" in report:
        print("❌ Found 'REFERENCES' in final report (Should be removed)")
    else:
        print("✅ Correctly removed REFERENCES from final report")
        
    if "## Conclusion" in report:
        print("✅ Found Conclusion")
    else:
        print("❌ Conclusion missing")

if __name__ == "__main__":
    asyncio.run(test_no_references())
