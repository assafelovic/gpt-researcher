#!/usr/bin/env python3
"""
Comprehensive test script for GPT-Researcher fallback mechanism debugging.

This script tests:
1. Fallback logic execution when primary providers fail
2. Debug logging of all LLM interactions including fallbacks
3. Proper retry history population
4. Error handling and logging

Usage:
    python test_fallback_debug.py
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gpt_researcher.llm_provider.generic.base import GenericLLMProvider  # noqa: E402
from gpt_researcher.llm_provider.generic.fallback import FallbackGenericLLMProvider  # noqa: E402
from gpt_researcher.utils.llm_debug_logger import get_llm_debug_logger, initialize_llm_debug_logger  # noqa: E402, F401


class MockFailingLLM:
    """Mock LLM that always fails to simulate primary provider failure"""

    def __init__(
        self,
        model_name: str = "mock-failing-model",
        error_message: str = "Mock failure",
    ):
        self.model_name: str = model_name
        self.model: str = model_name
        self.error_message: str = error_message
        self.temperature: float = 0.7
        self.max_tokens: int = 1000
        self.model_kwargs: dict[str, Any] = {}

    async def ainvoke(self, messages: list[dict[str, Any]]):
        """Always fail with a specific error"""
        raise Exception(f"Mock LLM failure: {self.error_message}")

    async def astream(self, messages: list[dict[str, Any]]):
        """Always fail with a specific error"""
        raise Exception(f"Mock LLM failure (streaming): {self.error_message}")


class MockSuccessLLM:
    """Mock LLM that always succeeds"""

    def __init__(
        self,
        model_name: str = "mock-success-model",
        response: str = "Mock successful response",
    ):
        self.model_name: str = model_name
        self.model: str = model_name
        self.response: str = response
        self.temperature: float = 0.7
        self.max_tokens: int = 1000
        self.model_kwargs: dict[str, Any] = {}

    async def ainvoke(self, messages: list[dict[str, Any]]):
        """Return a mock successful response"""

        class MockMessage:
            def __init__(self, content: str):
                self.content: str = content

        return MockMessage(self.response)

    async def astream(self, messages: list[dict[str, Any]]):
        """Stream a mock successful response"""

        class MockChunk:
            def __init__(self, content: str):
                self.content: str = content

        # Simulate streaming by yielding chunks
        words = self.response.split()
        for word in words:
            yield MockChunk(word + " ")
            await asyncio.sleep(0.01)  # Small delay to simulate streaming


async def test_fallback_mechanism():
    """Test the fallback mechanism with proper debug logging"""

    print("🧪 Starting Fallback Mechanism Test")
    print("=" * 60)

    # Create a temporary directory for debug logs
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize debug logger
        _debug_logger = initialize_llm_debug_logger(
            session_id="fallback_test", log_dir=temp_dir
        )

        print(f"📁 Debug logs will be saved to: {temp_dir}")

        # Create mock providers
        print("\n🔧 Setting up mock providers...")

        # Primary provider that will fail
        primary_llm = MockFailingLLM(
            "google/gemini-2.5-pro-exp-03-25", "No endpoints found"
        )
        _primary_provider = GenericLLMProvider(primary_llm, verbose=True)

        # Fallback providers - first one fails, second one succeeds
        fallback1_llm = MockFailingLLM("openai/gpt-4o", "Rate limit exceeded")
        fallback1_provider = GenericLLMProvider(fallback1_llm, verbose=True)

        fallback2_llm = MockSuccessLLM(
            "anthropic/claude-3-5-sonnet-20241022",
            "This is a successful fallback response from Claude.",
        )
        fallback2_provider = GenericLLMProvider(fallback2_llm, verbose=True)

        # Create fallback provider with multiple fallbacks
        fallback_provider = FallbackGenericLLMProvider(
            primary_llm,
            fallback_providers=[fallback1_provider, fallback2_provider],
            verbose=True,
        )

        print(f"✅ Primary: {primary_llm.model_name}")
        print(f"✅ Fallback 1: {fallback1_llm.model_name}")
        print(f"✅ Fallback 2: {fallback2_llm.model_name}")

        # Test messages
        test_messages = [
            {"role": "system", "content": "You are a helpful research assistant."},
            {
                "role": "user",
                "content": "Please provide the research report content for renewable energy developments.",
            },
        ]

        print(f"\n📝 Test messages prepared ({len(test_messages)} messages)")

        # Test the fallback mechanism
        print("\n🚀 Testing fallback mechanism...")
        start_time = time.time()

        try:
            response = await fallback_provider.get_chat_response(
                messages=test_messages, stream=False, websocket=None
            )

            duration = time.time() - start_time
            print(f"✅ SUCCESS: Got response in {duration:.2f}s")
            print(
                f"📄 Response: {response[:100]}{'...' if len(response) > 100 else ''}"
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ FAILED: {e.__class__.__name__}: {e}")
            print(f"⏱️ Failed after {duration:.2f}s")

        # Analyze debug logs
        print("\n🔍 Analyzing debug logs...")
        await analyze_debug_logs(temp_dir)

        return temp_dir


async def analyze_debug_logs(log_dir: str):
    """Analyze the debug logs to verify fallback mechanism worked correctly"""

    log_path = Path(log_dir)
    json_files = list(log_path.glob("llm_debug_*.json"))

    if not json_files:
        print("❌ No debug log files found!")
        return

    # Read the latest JSON log file
    latest_log = max(json_files, key=lambda f: f.stat().st_mtime)
    print(f"📖 Reading debug log: {latest_log.name}")

    try:
        with open(latest_log, "r", encoding="utf-8") as f:
            interactions = json.load(f)

        if not interactions:
            print("❌ No interactions found in debug log!")
            return

        print(f"📊 Found {len(interactions)} interaction(s)")

        # Analyze each interaction
        for i, interaction in enumerate(interactions):
            print(f"\n📋 Interaction {i + 1}:")
            print(f"   ID: {interaction.get('interaction_id', 'N/A')}")
            print(f"   Model: {interaction.get('model', 'N/A')}")
            print(f"   Provider: {interaction.get('provider', 'N/A')}")
            print(f"   Success: {interaction.get('success', 'N/A')}")
            print(f"   Is Fallback: {interaction.get('is_fallback', 'N/A')}")
            print(f"   Fallback Attempt: {interaction.get('fallback_attempt', 'N/A')}")
            print(f"   Primary Provider: {interaction.get('primary_provider', 'N/A')}")

            # Check retry history
            retry_history = interaction.get("retry_history", [])
            print(f"   Retry History: {len(retry_history)} entries")

            if retry_history:
                print("   📝 Retry Details:")
                for j, retry in enumerate(retry_history):
                    print(f"      {j + 1}. Attempt #{retry.get('attempt_number', 'N/A')}")
                    print(f"         Reason: {retry.get('reason', 'N/A')}")
                    details = retry.get("details", {})
                    if details:
                        print(f"         Details: {json.dumps(details, indent=10)}")
            else:
                print("   ⚠️  No retry history found!")

            # Check error information
            if not interaction.get("success", True):
                print(f"   ❌ Error Type: {interaction.get('error_type', 'N/A')}")
                print(f"   ❌ Error Message: {interaction.get('error_message', 'N/A')[:100]}...")

            # Check response
            response = interaction.get("response", "")
            if response:
                print(f"   ✅ Response Length: {len(response)} characters")
                print(f"   ✅ Response Preview: {response[:100]}{'...' if len(response) > 100 else ''}")

        # Summary analysis
        print("\n📈 SUMMARY ANALYSIS:")
        successful_interactions: int = sum(1 for i in interactions if i.get("success", False))
        fallback_interactions: int = sum(1 for i in interactions if i.get("is_fallback", False))
        total_retries: int = sum(len(i.get("retry_history", [])) for i in interactions)

        print(f"   Total Interactions: {len(interactions)}")
        print(f"   Successful: {successful_interactions}")
        print(f"   Failed: {len(interactions) - successful_interactions}")
        print(f"   Fallback Attempts: {fallback_interactions}")
        print(f"   Total Retry Entries: {total_retries}")

        # Validation
        print("\n✅ VALIDATION RESULTS:")
        if total_retries > 0:
            print("   ✅ Retry history is populated (fallback mechanism working)")
        else:
            print("   ❌ Retry history is empty (fallback mechanism not working)")

        if fallback_interactions > 0:
            print("   ✅ Fallback attempts were logged")
        else:
            print("   ❌ No fallback attempts were logged")

        if successful_interactions > 0:
            print("   ✅ At least one interaction succeeded")
        else:
            print("   ❌ All interactions failed")

    except Exception as e:
        print(f"❌ Error analyzing debug logs: {e.__class__.__name__}: {e}")


async def test_no_fallback_scenario():
    """Test scenario with no fallback providers"""

    print("\n🧪 Testing No-Fallback Scenario")
    print("=" * 40)

    # Create a temporary directory for debug logs
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize debug logger
        _debug_logger = initialize_llm_debug_logger(session_id="no_fallback_test", log_dir=temp_dir)

        # Primary provider that will fail (no fallbacks)
        primary_llm = MockFailingLLM("google/gemini-2.5-pro-exp-03-25", "No endpoints found")
        fallback_provider = FallbackGenericLLMProvider(
            primary_llm,
            fallback_providers=[],  # No fallbacks
            verbose=True,
        )

        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
        ]

        print("🚀 Testing with no fallback providers...")

        try:
            response = await fallback_provider.get_chat_response(messages=test_messages, stream=False, websocket=None)
            print(f"❌ Unexpected success: {response}")
        except Exception as e:
            print(f"✅ Expected failure: {e.__class__.__name__}: {str(e)[:100]}...")

        # Quick log analysis
        log_path = Path(temp_dir)
        json_files = list(log_path.glob("llm_debug_*.json"))
        if json_files:
            def _get_latest_log(json_files: list[Path]) -> Path:
                def _get_mtime(file: Path) -> float:
                    return file.stat().st_mtime
                return max(json_files, key=_get_mtime)

            latest_log: Path = _get_latest_log(json_files)
            interactions: list[dict[str, Any]] = json.loads(latest_log.read_text(encoding="utf-8"))

            if interactions:
                interaction = interactions[0]
                retry_count: int = len(interaction.get("retry_history", []))
                print(f"📊 Retry history entries: {retry_count}")
                if retry_count == 0:
                    print("✅ Correctly no retries when no fallbacks available")
                else:
                    print("❌ Unexpected retry entries when no fallbacks available")


async def main():
    """Main test function"""

    print("🔬 GPT-Researcher Fallback Mechanism Debug Test")
    print("=" * 80)
    print("This test validates:")
    print("1. ✅ Fallback logic properly executes when primary providers fail")
    print("2. ✅ All LLM interactions are comprehensively logged in debug logs")
    print("3. ✅ Retry history is properly populated with fallback attempts")
    print("4. ✅ Error handling works correctly")
    print("=" * 80)

    try:
        # Test 1: Full fallback mechanism
        await test_fallback_mechanism()

        # Test 2: No fallback scenario
        await test_no_fallback_scenario()

        print("\n🎉 All tests completed!")
        print(
            "Check the debug logs above to verify the fallback mechanism is working correctly."
        )

    except Exception as e:
        print(f"\n💥 Test failed with error: {e.__class__.__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
