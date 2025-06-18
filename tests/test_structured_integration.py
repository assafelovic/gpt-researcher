#!/usr/bin/env python3
"""Test script for structured research integration."""

from __future__ import annotations

import asyncio

from typing import Any

from gpt_researcher import GPTResearcher
from gpt_researcher.actions.report_analyzer import analyze_query_requirements, get_research_configuration


async def test_query_analysis() -> None:
    """Test the query analysis functionality."""

    test_queries: list[str] = [
        "Compare Docker vs Podman for enterprise container deployment",
        "What is machine learning and how does it work?",
        "Latest developments in quantum computing research",
        "Pros and cons of remote work policies",
        "How to implement microservices architecture",
    ]

    print("🧪 Testing Query Analysis\n")

    for query in test_queries:
        print(f"Query: {query}")

        # Mock config for testing
        class MockConfig:
            smart_llm_model: str = "gpt-4"
            smart_llm_provider: str = "openai"
            smart_token_limit: int = 1000
            llm_kwargs: dict[str, Any] = {}

        try:
            analysis: dict[str, Any] = await analyze_query_requirements(query, MockConfig())
            config: dict[str, Any] = get_research_configuration(analysis)

            print(f"  Report Style: {analysis.get('report_style')}")
            print(f"  User Expertise: {analysis.get('user_expertise')}")
            print(f"  Enable Structured: {config.get('enable_structured_research')}")
            print(f"  Enable Debate: {config.get('enable_debate')}")
            print(f"  Focus Areas: {analysis.get('focus_areas')}")
            print()

        except Exception as e:
            print(f"  ❌ Analysis failed: {e.__class__.__name__}: {e}")
            print()


async def test_structured_research_integration() -> None:
    """Test the structured research integration in GPTResearcher."""

    print("🔬 Testing Structured Research Integration\n")

    # Test query that should trigger structured research
    query: str = "Compare Docker Desktop vs Podman Desktop for Windows development"

    try:
        researcher: GPTResearcher = GPTResearcher(query=query, report_type="research_report", verbose=True)

        print(f"Query: {query}")
        print(f"Initial Tone: {researcher.tone}")

        # This should trigger query analysis and potentially update the tone
        context: list[str] = await researcher.conduct_research()

        print(f"Updated Tone: {researcher.tone}")
        print(f"Query Analysis: {researcher.query_analysis}")
        print(f"Research Config: {researcher.research_config}")
        print(f"Structured Pipeline Enabled: {researcher.structured_pipeline is not None}")
        print(f"Context Length: {len(context)}")

        # Test report generation (this would use structured research if enabled)
        # report = await researcher.write_report()
        # print(f"Report Length: {len(report)}")

    except Exception as e:
        print(f"❌ Integration test failed: {e.__class__.__name__}: {e}")


async def main() -> None:
    """Run all tests."""
    print("🚀 Testing Structured Research Integration\n")

    await test_query_analysis()
    await test_structured_research_integration()

    print("✅ Tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
