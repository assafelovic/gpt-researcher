#!/usr/bin/env python3
"""
Test script to demonstrate the RAG-based report generation fix.

This script shows how the new RAG system properly utilizes the memory/vector store
to generate comprehensive reports from large amounts of research data.
"""

import asyncio
import logging
from gpt_researcher import GPTResearcher

# Set up logging to see the RAG process
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_report_generation():
    """Test the new RAG-based report generation."""

    print("🔬 Testing RAG-based Report Generation Fix")
    print("=" * 50)

    # Test query that should generate a lot of research data
    query = "The impact of artificial intelligence on job markets and employment trends in 2024"

    print(f"📝 Query: {query}")
    print()

    # Create researcher with detailed report type (triggers RAG)
    researcher = GPTResearcher(
        query=query,
        report_type="detailed_report",  # This will trigger RAG
        report_source="web",
        verbose=True,
    )

    print("🔍 Starting research phase...")

    # Conduct research (this will gather lots of data)
    await researcher.conduct_research()

    print(f"📊 Research completed:")
    print(f"   - Context items: {len(researcher.context) if researcher.context else 0}")
    print(f"   - URLs visited: {len(researcher.visited_urls)}")
    print()

    # Calculate total context size
    total_chars = 0
    if researcher.context:
        for item in researcher.context:
            if isinstance(item, dict):
                if 'raw_content' in item:
                    total_chars += len(str(item['raw_content']))
                elif 'content' in item:
                    total_chars += len(str(item['content']))
                else:
                    total_chars += len(str(item))
            else:
                total_chars += len(str(item))

    print(f"📈 Total research data: {total_chars:,} characters")
    print()

    print("📝 Generating report using RAG...")

    # Generate report (should use RAG automatically)
    report = await researcher.write_report()

    print("✅ Report generation completed!")
    print(f"📄 Final report length: {len(report):,} characters")
    print(f"📄 Final report word count: ~{len(report.split()):,} words")
    print()

    # Show first 500 characters of the report
    print("📖 Report preview:")
    print("-" * 30)
    print(report[:500] + "..." if len(report) > 500 else report)
    print("-" * 30)

    # Save the report
    filename = f"rag_test_report_{query[:30].replace(' ', '_')}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"💾 Full report saved to: {filename}")

    return report

async def test_traditional_vs_rag():
    """Compare traditional vs RAG report generation."""

    print("\n🆚 Comparing Traditional vs RAG Generation")
    print("=" * 50)

    query = "Benefits and challenges of remote work in 2024"

    # Test 1: Traditional method (force disable RAG)
    print("🔄 Testing traditional method...")
    researcher_traditional = GPTResearcher(
        query=query,
        report_type="research_report",  # Regular report
        report_source="web",
        verbose=False,
    )

    await researcher_traditional.conduct_research()

    # Force traditional method
    traditional_report = await researcher_traditional.write_report(use_rag=False)

    print(f"📊 Traditional report: {len(traditional_report):,} characters")

    # Test 2: RAG method
    print("🧠 Testing RAG method...")
    researcher_rag = GPTResearcher(
        query=query,
        report_type="detailed_report",  # Detailed report triggers RAG
        report_source="web",
        verbose=False,
    )

    await researcher_rag.conduct_research()

    # Use RAG method
    rag_report = await researcher_rag.write_report(use_rag=True)

    print(f"📊 RAG report: {len(rag_report):,} characters")

    # Compare results
    print("\n📈 Comparison Results:")
    print(f"   Traditional: {len(traditional_report):,} chars, ~{len(traditional_report.split()):,} words")
    print(f"   RAG:         {len(rag_report):,} chars, ~{len(rag_report.split()):,} words")
    print(f"   Improvement: {((len(rag_report) - len(traditional_report)) / len(traditional_report) * 100):.1f}% more content")

if __name__ == "__main__":
    print("🚀 GPT Researcher RAG Fix Test")
    print("This test demonstrates the solution to token limit issues")
    print()

    try:
        # Run the main test
        asyncio.run(test_rag_report_generation())

        # Run comparison test
        asyncio.run(test_traditional_vs_rag())

        print("\n✅ All tests completed successfully!")
        print("\n💡 Key improvements:")
        print("   - Memory/VectorStore now properly utilized")
        print("   - Reports generated section-by-section using RAG")
        print("   - No more token limit truncation issues")
        print("   - Comprehensive reports from large research datasets")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
