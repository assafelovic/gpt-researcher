#!/usr/bin/env python3
"""
Test script to reproduce the detailed report conclusion issue
"""
from __future__ import annotations

import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.report_type.detailed_report.detailed_report import DetailedReport


async def test_detailed_report_conclusion():
    """Test the detailed report generation to see debug output"""
    print("=== Starting Detailed Report Test ===")

    # Create a simple detailed report
    report = DetailedReport(
        query="What are the latest developments in renewable energy?",
        report_type="detailed_report",
        report_source="web"
    )

    try:
        print("Running detailed report...")
        result = await report.run()

        print(f"\n=== FINAL REPORT LENGTH: {len(result)} ===")

        # Check if conclusion is present
        if "## Conclusion" in result:
            print("✅ Conclusion section found in report")
            # Extract conclusion section
            conclusion_start = result.find("## Conclusion")
            conclusion_section = result[conclusion_start:conclusion_start+500]
            print(f"Conclusion preview: {conclusion_section}...")
        else:
            print("❌ No conclusion section found in report")

        # Save the report for inspection
        with open("debug_test_report.md", "w") as f:
            f.write(result)
        print("Report saved to debug_test_report.md")

    except Exception as e:
        print(f"❌ Error during report generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_detailed_report_conclusion())
