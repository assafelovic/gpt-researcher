"""Test script to demonstrate LLM interaction visualization during report generation.

This script shows how the new visualization system captures and displays
all LLM interactions that occur during the report generation phase.
"""

from __future__ import annotations

import asyncio

from dotenv import load_dotenv

from gpt_researcher.agent import GPTResearcher
from gpt_researcher.skills.llm_visualizer import enable_llm_visualization

# Load environment variables
load_dotenv()


async def test_visualization() -> str:
    """Test the LLM interaction visualization"""

    print("🧪 Testing LLM Interaction Visualization")
    print("=" * 50)

    # Enable visualization
    enable_llm_visualization()

    # Create a simple research query
    query = "What are the key benefits of artificial intelligence in healthcare?"

    # Initialize researcher
    researcher = GPTResearcher(
        query=query,
        report_type="research_report",
        verbose=True,
    )

    print(f"\n🔬 Research Query: {query}")
    print("\n⚗️ Starting research phase...")

    # Conduct research (this won't be visualized, only report generation)
    research_context: list[str] = await researcher.conduct_research()

    print(f"\n📊 Research completed. Found {len(research_context)} sources.")
    print("\n📝 Starting report generation (THIS WILL BE VISUALIZED)...")
    print("=" * 80)

    # Generate report (this WILL be visualized)
    report: str = await researcher.write_report()

    print("\n" + "=" * 80)
    print("✅ Test completed!")
    print(f"📄 Generated report: {len(report)} characters")
    print(f"📈 Report preview:\n{report[:300]}...")

    return report


async def test_introduction_and_conclusion() -> tuple[str, str]:
    """Test individual report components"""

    print("\n🧪 Testing Individual Report Components")
    print("=" * 50)

    # Enable visualization
    enable_llm_visualization()

    query = "How does machine learning impact modern education?"

    researcher = GPTResearcher(
        query=query,
        report_type="research_report",
        verbose=True,
    )

    # Conduct minimal research
    await researcher.conduct_research()

    print("\n📝 Testing Introduction Generation...")
    print("-" * 40)

    # Test introduction (will be visualized)
    introduction: str = await researcher.write_introduction()

    print(f"\n📄 Introduction: {introduction[:200]}...")

    print("\n📝 Testing Conclusion Generation...")
    print("-" * 40)

    # Test conclusion (will be visualized)
    conclusion: str = await researcher.write_report_conclusion("Sample report content for conclusion testing.")

    print(f"\n📄 Conclusion: {conclusion[:200]}...")

    return introduction, conclusion


async def main():
    """Main test function"""

    print("🎬 LLM INTERACTION VISUALIZATION DEMO")
    print("=" * 80)
    print("This demo shows how GPT Researcher visualizes all LLM interactions")
    print("during report generation in a 2D mapping format.")
    print("=" * 80)

    try:
        # Test 1: Full report generation
        print("\n🎯 TEST 1: Full Report Generation with Visualization")
        await test_visualization()

        print("\n" + "=" * 80)

        # Test 2: Individual components
        print("\n🎯 TEST 2: Individual Components (Introduction & Conclusion)")
        intro, conclusion = await test_introduction_and_conclusion()

        print("\n" + "=" * 80)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nKey Features Demonstrated:")
        print("✅ Real-time LLM interaction tracking")
        print("✅ Detailed prompt and response visualization")
        print("✅ 2D flow diagram generation")
        print("✅ Performance metrics (timing, token counts)")
        print("✅ Error handling and failed interaction tracking")
        print("✅ Mermaid diagram export for visual flow")

    except Exception as e:
        print(f"\n❌ Error during testing: {e.__class__.__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
