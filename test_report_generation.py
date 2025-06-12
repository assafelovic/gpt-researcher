#!/usr/bin/env python3
"""Test script to verify report generation fixes."""
from __future__ import annotations

import asyncio
import logging

from gpt_researcher.actions.report_generation import generate_report
from gpt_researcher.config.config import Config
from gpt_researcher.utils.enum import Tone

# Set up logging
logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


async def test_report_generation():
    """Test report generation with token limit fixes."""
    print("=" * 80)
    print("TESTING REPORT GENERATION WITH TOKEN LIMIT FIXES")
    print("=" * 80)

    cfg = Config()
    print(f"Primary model: {cfg.smart_llm_model}")
    print(f"Primary provider: {cfg.smart_llm_provider}")
    print(f"Token limit: {cfg.smart_token_limit}")
    print(f"Fallback providers: {len(cfg.smart_llm_fallback_providers)}")
    print()

    # Test with a simple query that should work
    print("🧪 Test 1: Simple Report Generation")
    print("-" * 50)

    try:
        report: str = await generate_report(
            query="What is artificial intelligence?",
            context="Artificial intelligence (AI) is a branch of computer science that aims to create intelligent machines that can perform tasks that typically require human intelligence. AI systems can learn, reason, and make decisions.",
            agent_role_prompt="You are a helpful research assistant. Write a clear and concise report.",
            report_type="research_report",
            tone=Tone.Objective,
            report_source="web",
            websocket=None,
            cfg=cfg
        )

        if report and len(report) > 0:
            print(f"✅ Success! Report generated: {len(report)} characters")
            print(f"Report preview: {report[:200]}...")
        else:
            print("❌ Failed: Empty report generated")

    except Exception as e:
        print(f"❌ Error: {e.__class__.__name__}: {e}")
        import traceback
        traceback.print_exc()

    print()

    # Test with a larger context that might trigger token reduction
    print("🧪 Test 2: Large Context Report Generation")
    print("-" * 50)

    large_context: str = """
    Artificial intelligence (AI) is a rapidly evolving field that encompasses various technologies and approaches.
    """ + "This is a test sentence that will be repeated many times to create a large context. " * 500

    try:
        report = await generate_report(
            query="Summarize the key aspects of artificial intelligence",
            context=large_context,
            agent_role_prompt="You are a helpful research assistant. Write a comprehensive report based on the provided context.",
            report_type="research_report",
            tone=Tone.Objective,
            report_source="web",
            websocket=None,
            cfg=cfg
        )

        if report and len(report) > 0:
            print(f"✅ Success! Large context report generated: {len(report)} characters")
            print(f"Report preview: {report[:200]}...")
        else:
            print("❌ Failed: Empty report generated for large context")

    except Exception as e:
        print(f"❌ Error with large context: {e.__class__.__name__}: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print("REPORT GENERATION TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_report_generation())
