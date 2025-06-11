#!/usr/bin/env python3
"""Comprehensive test script combining all GPT-Researcher test functionality."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from gpt_researcher.config.config import Config

# Add current directory to path
sys.path.insert(0, ".")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger: logging.Logger = logging.getLogger(__name__)


async def test_llm_fallbacks_loading() -> bool:
    """Test llm_fallbacks loading functionality."""
    print("\n" + "=" * 80)
    print("SECTION 1: TESTING LLM_FALLBACKS LOADING")
    print("=" * 80)

    try:
        from llm_fallbacks.config import (
            ALL_MODELS,
            CUSTOM_PROVIDERS,
            FREE_MODELS,
            LiteLLMBaseModelSpec,
        )

        print("✅ Successfully loaded llm_fallbacks")
        print(f"   - Total ALL_MODELS: {len(ALL_MODELS)}")
        print(f"   - Total FREE_MODELS: {len(FREE_MODELS)}")
        print(f"   - Custom providers: {len(CUSTOM_PROVIDERS)}")

        # Check OpenRouter models
        openrouter_models: list[tuple[str, LiteLLMBaseModelSpec]] = [
            m for m in ALL_MODELS if "openrouter" in m[0].lower()
        ]
        free_openrouter: list[tuple[str, LiteLLMBaseModelSpec]] = [
            m for m in FREE_MODELS if "openrouter" in m[0].lower()
        ]

        print(f"   - OpenRouter models in ALL_MODELS: {len(openrouter_models)}")
        print(f"   - OpenRouter models in FREE_MODELS: {len(free_openrouter)}")

        if FREE_MODELS:
            print("\n🔍 First 3 FREE_MODELS:")
            for i, (model_name, spec) in enumerate(FREE_MODELS[:3]):
                provider: str = spec.get("litellm_provider", "unknown")
                mode: str = spec.get("mode", "unknown")
                print(f"   {i + 1}. {model_name} (provider: {provider}, mode: {mode})")

        return True

    except Exception as e:
        print(f"❌ Error loading llm_fallbacks: {e.__class__.__name__}: {e}")
        return False


async def test_manual_defaults() -> bool:
    """Test manual defaults loading and 'auto' resolution functionality."""
    print("\n" + "=" * 80)
    print("SECTION 2: TESTING MANUAL DEFAULTS AND AUTO RESOLUTION")
    print("=" * 80)

    try:
        from gpt_researcher.config.variables.default import DEFAULT_CONFIG
        from gpt_researcher.config.config import Config

        print("✅ Successfully loaded manual defaults")

        # Show raw config values before resolution
        fast_llm_raw: str = DEFAULT_CONFIG.get("FAST_LLM", "")
        smart_llm_raw: str = DEFAULT_CONFIG.get("SMART_LLM", "")
        strategic_llm_raw: str = DEFAULT_CONFIG.get("STRATEGIC_LLM", "")
        fast_fallbacks: str = DEFAULT_CONFIG.get("FAST_LLM_FALLBACKS", "")
        smart_fallbacks: str = DEFAULT_CONFIG.get("SMART_LLM_FALLBACKS", "")
        strategic_fallbacks: str = DEFAULT_CONFIG.get("STRATEGIC_LLM_FALLBACKS", "")

        print("\n📋 RAW CONFIG VALUES (before 'auto' resolution):")
        print(f"   - FAST_LLM: '{fast_llm_raw}'")
        print(f"   - SMART_LLM: '{smart_llm_raw}'")
        print(f"   - STRATEGIC_LLM: '{strategic_llm_raw}'")
        print(f"   - FAST_LLM_FALLBACKS: '{fast_fallbacks}' (length: {len(fast_fallbacks.split(',')) if fast_fallbacks else 0})")
        print(f"   - SMART_LLM_FALLBACKS: '{smart_fallbacks}' (length: {len(smart_fallbacks.split(',')) if smart_fallbacks else 0})")
        print(f"   - STRATEGIC_LLM_FALLBACKS: '{strategic_fallbacks}' (length: {len(strategic_fallbacks.split(',')) if strategic_fallbacks else 0})")

        # Now test 'auto' resolution by creating a Config instance
        print("\n🔧 Testing 'auto' resolution by initializing Config...")

        # Set environment to use 'auto' values
        import os
        os.environ["FAST_LLM"] = "auto"
        os.environ["SMART_LLM"] = "auto"
        os.environ["STRATEGIC_LLM"] = "auto"

        config = Config()

        print("\n📋 RESOLVED VALUES (after 'auto' resolution):")
        print(f"   - FAST_LLM: '{getattr(config, 'fast_llm', 'Not set')}'")
        print(f"   - SMART_LLM: '{getattr(config, 'smart_llm', 'Not set')}'")
        print(f"   - STRATEGIC_LLM: '{getattr(config, 'strategic_llm', 'Not set')}'")

        # Show fallback counts for all three types
        fast_count: int = len(getattr(config, "fast_llm_fallback_providers", []))
        smart_count: int = len(getattr(config, "smart_llm_fallback_providers", []))
        strategic_count: int = len(getattr(config, "strategic_llm_fallback_providers", []))

        print(f"   - FAST_LLM fallback providers: {fast_count}")
        print(f"   - SMART_LLM fallback providers: {smart_count}")
        print(f"   - STRATEGIC_LLM fallback providers: {strategic_count}")

        # Show first few fallback models for each type
        print("\n🔍 First 3 resolved fallback models for each type:")

        # Fast LLM fallbacks
        if hasattr(config, 'fast_llm_fallback_providers') and config.fast_llm_fallback_providers:
            print("   FAST_LLM fallbacks:")
            for i, provider in enumerate(config.fast_llm_fallback_providers[:3]):
                model_name = getattr(provider, 'model', 'Unknown')
                provider_name = getattr(provider, 'llm_provider', 'Unknown')
                print(f"     {i + 1}. {provider_name}:{model_name}")

        # Smart LLM fallbacks
        if hasattr(config, 'smart_llm_fallback_providers') and config.smart_llm_fallback_providers:
            print("   SMART_LLM fallbacks:")
            for i, provider in enumerate(config.smart_llm_fallback_providers[:3]):
                model_name = getattr(provider, 'model', 'Unknown')
                provider_name = getattr(provider, 'llm_provider', 'Unknown')
                print(f"     {i + 1}. {provider_name}:{model_name}")

        # Strategic LLM fallbacks
        if hasattr(config, 'strategic_llm_fallback_providers') and config.strategic_llm_fallback_providers:
            print("   STRATEGIC_LLM fallbacks:")
            for i, provider in enumerate(config.strategic_llm_fallback_providers[:3]):
                model_name = getattr(provider, 'model', 'Unknown')
                provider_name = getattr(provider, 'llm_provider', 'Unknown')
                print(f"     {i + 1}. {provider_name}:{model_name}")

        return True

    except Exception as e:
        print(f"❌ Error loading manual defaults or resolving 'auto': {e.__class__.__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fallback_conversion(
    llm_fallbacks_loaded: bool,
) -> bool:
    """Test fallback conversion functionality."""
    print("\n" + "=" * 80)
    print("SECTION 3: TESTING FALLBACK CONVERSION")
    print("=" * 80)

    try:
        if llm_fallbacks_loaded:
            from gpt_researcher.config.fallback_logic import generate_auto_fallbacks_from_free_models
            from llm_fallbacks.config import FREE_MODELS

            print("🔧 Testing fallback conversion...")

            if FREE_MODELS:
                # Test conversion for fast_chat
                converted: list[str] = generate_auto_fallbacks_from_free_models(
                    FREE_MODELS,
                    "fast_chat",
                    "",  # No primary model to exclude
                    2000,  # fast_token_limit
                    4000,  # smart_token_limit
                    4000,  # strategic_token_limit
                    verbose_logging=True,
                )

                print(f"✅ Conversion successful: {len(converted)} models converted")
                if converted:
                    print("🔍 First 3 converted models:")
                    for i, model in enumerate(converted[:3]):
                        print(f"   {i + 1}. {model}")

                return True
            else:
                print("❌ No FREE_MODELS available for conversion test")
                return False
        else:
            print("⏭️ Skipping fallback conversion (llm_fallbacks not loaded)")
            return False

    except Exception as e:
        print(f"❌ Error in fallback conversion: {e.__class__.__name__}: {e}")
        return False


async def test_format_conversion() -> bool:
    """Test format conversion functionality."""
    print("\n" + "=" * 80)
    print("SECTION 4: TESTING FORMAT CONVERSION")
    print("=" * 80)

    try:
        from gpt_researcher.config.fallback_logic import parse_model_fallbacks

        # Test auto generation for different model types
        test_cases: list[tuple[str, str]] = [
            ("fast_chat", "FAST_LLM"),
            ("strategic_chat", "STRATEGIC_LLM"),
            ("chat", "SMART_LLM"),
        ]

        format_test_passed: bool = True

        for model_type, display_name in test_cases:
            print(f"\n📋 Testing {display_name} ({model_type}):")

            # Generate auto fallbacks
            auto_fallbacks: list[str] = parse_model_fallbacks(
                fallbacks_str="auto",
                model_type=model_type,
                primary_model_id="",  # Empty to avoid filtering
                fast_token_limit=2000,
                smart_token_limit=4000,
                strategic_token_limit=4000,
            )

            print(f"   Generated {len(auto_fallbacks)} auto fallbacks")

            # Check format patterns
            format_stats: dict[str, int] = {
                "openrouter_with_free": 0,
                "gemini_with_free": 0,
                "other_with_free": 0,
                "missing_free_suffix": 0,
                "total": len(auto_fallbacks),
            }

            openrouter_models: list[str] = []
            first_5_models: list[str] = []

            for i, fallback in enumerate(auto_fallbacks):
                if i < 5:
                    first_5_models.append(fallback)

                if fallback.startswith("openrouter:") and fallback.endswith(":free"):
                    format_stats["openrouter_with_free"] += 1
                    if len(openrouter_models) < 3:
                        openrouter_models.append(fallback)
                elif fallback.startswith("gemini:") and fallback.endswith(":free"):
                    format_stats["gemini_with_free"] += 1
                elif fallback.endswith(":free"):
                    format_stats["other_with_free"] += 1
                else:
                    format_stats["missing_free_suffix"] += 1

            # Display results
            print(f"   ✅ OpenRouter models with :free suffix: {format_stats['openrouter_with_free']}")
            print(f"   ✅ Gemini models with :free suffix: {format_stats['gemini_with_free']}")
            print(f"   ✅ Other models with :free suffix: {format_stats['other_with_free']}")

            if format_stats["missing_free_suffix"] > 0:
                print(
                    f"   ❌ Models missing :free suffix: {format_stats['missing_free_suffix']}"
                )
                format_test_passed = False

            # Show first 5 generated models
            print("   📝 First 5 generated models:")
            for i, model in enumerate(first_5_models, 1):
                print(f"       {i}. {model}")

            # Check if OpenRouter models come first
            if auto_fallbacks:
                openrouter_first: bool = auto_fallbacks[0].startswith("openrouter:")
                if openrouter_first:
                    print("   ✅ OpenRouter model prioritized first")
                else:
                    print(f"   ⚠️ First model is not OpenRouter: {auto_fallbacks[0]}")

        return format_test_passed

    except Exception as e:
        print(f"❌ Error during format conversion test: {e.__class__.__name__}: {e}")
        return False


async def test_config_loading() -> tuple[bool, Any]:
    """Test configuration loading and logging functionality."""
    print("\n" + "=" * 80)
    print("SECTION 5: TESTING CONFIGURATION LOADING AND LOGGING")
    print("=" * 80)

    try:
        # Set environment variables for testing
        os.environ["FAST_LLM"] = "auto"
        os.environ["SMART_LLM"] = "auto"
        os.environ["STRATEGIC_LLM"] = "auto"

        from gpt_researcher.config.config import Config

        print("🔧 Initializing GPT Researcher configuration...")
        config = Config()

        print("\n📋 CONFIGURATION SUMMARY:")
        print(f"   Fast LLM: {getattr(config, 'fast_llm', 'Not set')}")
        print(f"   Smart LLM: {getattr(config, 'smart_llm', 'Not set')}")
        print(f"   Strategic LLM: {getattr(config, 'strategic_llm', 'Not set')}")
        print(f"   Retrievers: {getattr(config, 'retrievers', 'Not set')}")
        print(f"   Document Path: {getattr(config, 'doc_path', 'Not set')}")

        # Show fallback provider counts
        fast_count: int = len(getattr(config, "fast_llm_fallback_providers", []))
        smart_count: int = len(getattr(config, "smart_llm_fallback_providers", []))
        strategic_count: int = len(
            getattr(config, "strategic_llm_fallback_providers", [])
        )

        print(f"   ⚡ Fast LLM Fallbacks: {fast_count} providers")
        print(f"   🧠 Smart LLM Fallbacks: {smart_count} providers")
        print(f"   🎯 Strategic LLM Fallbacks: {strategic_count} providers")

        print("✅ Configuration loaded successfully!")
        return True, config

    except Exception as e:
        print(f"❌ Error during configuration loading: {e.__class__.__name__}: {e}")
        return False, None


async def test_fallback_mechanism(
    config_loaded: bool,
    config: Config,
) -> dict[str, bool]:
    """Test fallback mechanism functionality."""
    print("\n" + "=" * 80)
    print("SECTION 6: TESTING FALLBACK MECHANISM")
    print("=" * 80)

    fallback_results: dict[str, bool] = {
        "simple_fallback": False,
        "large_context_fallback": False,
        "invalid_model_fallback": False,
    }

    if not config_loaded:
        print("⏭️ Skipping fallback mechanism testing (config not loaded)")
        return fallback_results

    try:
        from gpt_researcher.utils.llm import create_chat_completion

        print("📋 Configuration Summary:")
        print(f"   Smart LLM: {config.smart_llm}")
        print(f"   Smart LLM Provider: {config.smart_llm_provider}")
        print(f"   Smart LLM Model: {config.smart_llm_model}")
        print(f"   Available Fallback Providers: {len(config.smart_llm_fallback_providers)}")

        if config.smart_llm_fallback_providers:
            print("   Fallback Models:")
            for i, provider in enumerate(config.smart_llm_fallback_providers):
                model_name: str = getattr(provider.llm, "model_name", None) or getattr(
                    provider.llm,
                    "model",
                    "unknown",
                )
                print(f"     {i + 1}. {model_name}")

            print("\n🧪 Test 1: Simple Request")
            print("-" * 40)

            messages: list[dict[str, str]] = [
                {
                    "role": "user",
                    "content": "Say 'Hello, this is a test response!' and nothing else.",
                }
            ]

            try:
                response: str = await create_chat_completion(
                    messages=messages,
                    model=config.smart_llm_model,
                    llm_provider=config.smart_llm_provider,
                    cfg=config,
                    max_tokens=50,
                )
                print(f"✅ Success! Response: {response}")
                fallback_results["simple_fallback"] = True

            except Exception as e:
                print(f"❌ Failed: {e.__class__.__name__}: {e}")

            print("\n🧪 Test 2: Large Context Request")
            print("-" * 40)

            # Create a large context
            large_content: str = "This is a test sentence. " * 1000
            large_messages: list[dict[str, str]] = [
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": f"Please summarize this text in one sentence: {large_content}",
                },
            ]

            try:
                response: str = await create_chat_completion(
                    messages=large_messages,
                    model=config.smart_llm_model,
                    llm_provider=config.smart_llm_provider,
                    cfg=config,
                    max_tokens=100,
                )
                print(f"✅ Success! Response: {response[:200]}...")
                fallback_results["large_context_fallback"] = True

            except Exception as e:
                print(f"❌ Failed: {type(e).__name__}: {e}")

            print("\n🧪 Test 3: Invalid Model")
            print("-" * 40)

            try:
                response: str = await create_chat_completion(
                    messages=messages,
                    model="invalid-model-that-does-not-exist",
                    llm_provider=config.smart_llm_provider,
                    cfg=config,
                    max_tokens=50,
                )
                print(f"✅ Success with fallback! Response: {response}")
                fallback_results["invalid_model_fallback"] = True

            except Exception as e:
                print(f"❌ All providers failed: {e.__class__.__name__}: {e}")

        else:
            print("⚠️ No fallback providers configured!")

    except Exception as e:
        print(f"❌ Error in fallback mechanism testing: {e.__class__.__name__}: {e}")

    return fallback_results


async def test_report_generation(
    config_loaded: bool,
    config: Config,
) -> dict[str, bool]:
    """Test report generation functionality."""
    print("\n" + "=" * 80)
    print("SECTION 7: TESTING REPORT GENERATION")
    print("=" * 80)

    report_results: dict[str, bool] = {
        "simple_report": False,
        "large_context_report": False,
    }

    if not config_loaded:
        print("⏭️ Skipping report generation testing (config not loaded)")
        return report_results

    try:
        from gpt_researcher.actions.report_generation import generate_report
        from gpt_researcher.utils.enum import Tone

        print(f"Primary model: {config.smart_llm_model}")
        print(f"Primary provider: {config.smart_llm_provider}")
        print(f"Token limit: {config.smart_token_limit}")

        print("\n🧪 Test 1: Simple Report Generation")
        print("-" * 40)

        try:
            report: str = await generate_report(
                query="What is artificial intelligence?",
                context="Artificial intelligence (AI) is a branch of computer science that aims to create intelligent machines that can perform tasks that typically require human intelligence. AI systems can learn, reason, and make decisions.",
                agent_role_prompt="You are a helpful research assistant. Write a clear and concise report.",
                report_type="research_report",
                tone=Tone.Objective,
                report_source="web",
                websocket=None,
                cfg=config,
            )

            if report and len(report) > 0:
                print(f"✅ Success! Report generated: {len(report)} characters")
                print(f"Report preview: {report[:200]}...")
                report_results["simple_report"] = True
            else:
                print("❌ Failed: Empty report generated")
        except Exception as e:
            print(f"❌ Error: {e.__class__.__name__}: {e}")

        print("\n🧪 Test 2: Large Context Report Generation")
        print("-" * 40)

        large_context: str = (
            """Artificial intelligence (AI) is a rapidly evolving field that encompasses various technologies and approaches."""
            + "This is a test sentence that will be repeated many times to create a large context. "
            * 500
        )

        try:
            report = await generate_report(
                query="Summarize the key aspects of artificial intelligence",
                context=large_context,
                agent_role_prompt="You are a helpful research assistant. Write a comprehensive report based on the provided context.",
                report_type="research_report",
                tone=Tone.Objective,
                report_source="web",
                websocket=None,
                cfg=config,
            )

            if report and len(report) > 0:
                print(f"✅ Success! Large context report generated: {len(report)} characters")
                print(f"Report preview: {report[:200]}...")
                report_results["large_context_report"] = True
            else:
                print("❌ Failed: Empty report generated for large context")
        except Exception as e:
            print(f"❌ Error with large context: {e.__class__.__name__}: {e}")

    except Exception as e:
        print(f"❌ Error in report generation testing: {e.__class__.__name__}: {e}")

    return report_results


async def display_results_summary(test_results: dict[str, bool]) -> None:
    """Display a summary of all test results."""
    print("\n" + "=" * 100)
    print("COMPREHENSIVE TEST RESULTS SUMMARY")
    print("=" * 100)

    total_tests: int = len(test_results)
    passed_tests: int = sum(test_results.values())

    print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed")
    print()

    for test_name, passed in test_results.items():
        status: str = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")

    print("\n" + "=" * 100)
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! GPT-Researcher is working correctly.")
    else:
        print(f"⚠️ {total_tests - passed_tests} test(s) failed. Please review the output above.")
    print("=" * 100)


async def comprehensive_test() -> dict[str, bool]:
    """Comprehensive test function that combines all GPT-Researcher test functionality.

    This function tests:
    1. Fallback mechanism with various scenarios
    2. llm_fallbacks loading and comparison
    3. Format conversion fixes
    4. Improved logging functionality
    5. Report generation with token limits
    """
    print("=" * 100)
    print("GPT-RESEARCHER COMPREHENSIVE TEST SUITE")
    print("=" * 100)

    test_results: dict[str, bool] = {}

    # Run individual test functions
    test_results["llm_fallbacks_loading"] = await test_llm_fallbacks_loading()
    test_results["manual_defaults"] = await test_manual_defaults()
    test_results["fallback_conversion"] = await test_fallback_conversion(test_results["llm_fallbacks_loading"])
    test_results["format_conversion"] = await test_format_conversion()

    config_loaded, config = await test_config_loading()
    test_results["config_loading"] = config_loaded

    fallback_results: dict[str, bool] = await test_fallback_mechanism(
        config_loaded,
        config,
    )
    test_results.update(fallback_results)

    report_results: dict[str, bool] = await test_report_generation(
        config_loaded,
        config,
    )
    test_results.update(report_results)

    await display_results_summary(test_results)

    return test_results


if __name__ == "__main__":
    asyncio.run(comprehensive_test())
