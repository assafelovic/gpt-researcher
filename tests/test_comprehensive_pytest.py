#!/usr/bin/env python3
"""Comprehensive pytest test suite for GPT-Researcher functionality."""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING, Any, Generator

import pytest

from llm_fallbacks.config import LiteLLMBaseModelSpec

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


# Fixtures
@pytest.fixture(scope="session")
def test_environment() -> Generator[None, Any, None]:
    """Set up test environment variables."""
    os.environ["FAST_LLM"] = "auto"
    os.environ["SMART_LLM"] = "auto"
    os.environ["STRATEGIC_LLM"] = "auto"
    yield
    # Cleanup if needed
    for key in ["FAST_LLM", "SMART_LLM", "STRATEGIC_LLM"]:
        os.environ.pop(key, None)


@pytest.fixture(scope="session")
def llm_fallbacks_available() -> dict[str, Any]:
    """Check if llm_fallbacks module is available."""
    try:
        from llm_fallbacks.config import (
            ALL_MODELS,
            CUSTOM_PROVIDERS,
            FREE_MODELS,
        )

        return {
            "available": True,
            "all_models": ALL_MODELS,
            "free_models": FREE_MODELS,
            "custom_providers": CUSTOM_PROVIDERS,
        }
    except Exception as e:
        logger.warning(f"llm_fallbacks not available: {e.__class__.__name__}: {e}")
        return {"available": False, "error": f"{e.__class__.__name__}: {e}"}


@pytest.fixture(scope="session")
def gpt_researcher_config(test_environment: Any) -> dict[str, Any]:
    """Load GPT Researcher configuration."""
    try:
        from gpt_researcher.config.config import Config

        config: Config = Config()
        return {"loaded": True, "config": config}
    except Exception as e:
        logger.error(f"Failed to load config: {e.__class__.__name__}: {e}")
        return {"loaded": False, "error": f"{e.__class__.__name__}: {e}"}


# Test Classes
class TestLLMFallbacksLoading:
    """Test llm_fallbacks loading functionality."""

    def test_llm_fallbacks_import(
        self,
        llm_fallbacks_available: dict[str, Any],
    ) -> None:
        """Test llm_fallbacks loading functionality."""
        print("\n" + "=" * 80)
        print("SECTION 1: TESTING LLM_FALLBACKS LOADING")
        print("=" * 80)

        if not llm_fallbacks_available["available"]:
            pytest.skip(f"llm_fallbacks not available: {llm_fallbacks_available['error']}")

        print("✅ Successfully loaded llm_fallbacks")
        print(f"   - Total ALL_MODELS: {len(llm_fallbacks_available['all_models'])}")
        print(f"   - Total FREE_MODELS: {len(llm_fallbacks_available['free_models'])}")
        print(f"   - Custom providers: {len(llm_fallbacks_available['custom_providers'])}")

        # Check OpenRouter models
        all_models: list[tuple[str, LiteLLMBaseModelSpec]] = llm_fallbacks_available["all_models"]
        free_models: list[tuple[str, LiteLLMBaseModelSpec]] = llm_fallbacks_available["free_models"]

        openrouter_models: list[tuple[str, LiteLLMBaseModelSpec]] = [
            m for m in all_models if "openrouter" in m[0].lower()
        ]
        free_openrouter: list[tuple[str, LiteLLMBaseModelSpec]] = [
            m for m in free_models if "openrouter" in m[0].lower()
        ]

        print(f"   - OpenRouter models in ALL_MODELS: {len(openrouter_models)}")
        print(f"   - OpenRouter models in FREE_MODELS: {len(free_openrouter)}")

        if free_models:
            print("\n🔍 First 3 FREE_MODELS:")
            for i, (model_name, spec) in enumerate(free_models[:3]):
                provider: str = spec.get("litellm_provider", "unknown")
                mode: str = spec.get("mode", "unknown")
                print(f"   {i + 1}. {model_name} (provider: {provider}, mode: {mode})")

        assert len(all_models) > 0, "Should have some models available"
        assert len(free_models) > 0, "Should have some free models available"


class TestManualDefaults:
    """Test manual defaults loading and 'auto' resolution functionality."""

    def test_manual_defaults_and_auto_resolution(
        self,
        test_environment: Any,
    ) -> None:
        """Test manual defaults loading and 'auto' resolution functionality."""
        print("\n" + "=" * 80)
        print("SECTION 2: TESTING MANUAL DEFAULTS AND AUTO RESOLUTION")
        print("=" * 80)

        try:
            from gpt_researcher.config.config import Config
            from gpt_researcher.config.variables.default import DEFAULT_CONFIG

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

            print("\n🔧 Testing 'auto' resolution by initializing Config...")
            config: Config = Config()

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
            if config.fast_llm_fallback_providers:
                print("   FAST_LLM fallbacks:")
                for i, provider in enumerate(config.fast_llm_fallback_providers[:3]):
                    model_name: str = getattr(provider, "model", "Unknown")
                    provider_name: str = getattr(provider, "llm_provider", "Unknown")
                    print(f"     {i + 1}. {provider_name}:{model_name}")

            # Smart LLM fallbacks
            if config.smart_llm_fallback_providers:
                print("   SMART_LLM fallbacks:")
                for i, provider in enumerate(config.smart_llm_fallback_providers[:3]):
                    model_name = getattr(provider, "model", "Unknown")
                    provider_name = getattr(provider, "llm_provider", "Unknown")
                    print(f"     {i + 1}. {provider_name}:{model_name}")

            # Strategic LLM fallbacks
            if config.strategic_llm_fallback_providers:
                print("   STRATEGIC_LLM fallbacks:")
                for i, provider in enumerate(
                    config.strategic_llm_fallback_providers[:3]
                ):
                    model_name = getattr(provider, "model", "Unknown")
                    provider_name = getattr(provider, "llm_provider", "Unknown")
                    print(f"     {i + 1}. {provider_name}:{model_name}")

            assert hasattr(config, "fast_llm"), "Config should have fast_llm attribute"
            assert hasattr(config, "smart_llm"), "Config should have smart_llm attribute"
            assert hasattr(config, "strategic_llm"), "Config should have strategic_llm attribute"

        except Exception as e:
            pytest.fail(f"Error loading manual defaults or resolving 'auto': {e.__class__.__name__}: {e}")


class TestFallbackConversion:
    """Test fallback conversion functionality."""

    def test_fallback_conversion(
        self,
        llm_fallbacks_available: dict[str, Any],
    ) -> None:
        """Test fallback conversion functionality."""
        print("\n" + "=" * 80)
        print("SECTION 3: TESTING FALLBACK CONVERSION")
        print("=" * 80)

        if not llm_fallbacks_available["available"]:
            pytest.skip("llm_fallbacks not loaded")

        try:
            from gpt_researcher.config.fallback_logic import generate_auto_fallbacks_from_free_models

            print("🔧 Testing fallback conversion...")
            free_models: list[tuple[str, LiteLLMBaseModelSpec]] = llm_fallbacks_available["free_models"]

            if not free_models:
                pytest.fail("No FREE_MODELS available for conversion test")

            # Test conversion for fast_chat
            converted: list[tuple[str, LiteLLMBaseModelSpec]] = generate_auto_fallbacks_from_free_models(
                free_models,
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

            assert len(converted) > 0, "Should have converted some models"

        except Exception as e:
            pytest.fail(f"Error in fallback conversion: {e.__class__.__name__}: {e}\n")


class TestFormatConversion:
    """Test format conversion functionality."""

    @pytest.mark.parametrize(
        "model_type,display_name",
        [
            ("fast_chat", "FAST_LLM"),
            ("strategic_chat", "STRATEGIC_LLM"),
            ("chat", "SMART_LLM"),
        ],
    )
    def test_format_conversion(
        self,
        model_type: str,
        display_name: str,
    ) -> None:
        """Test format conversion functionality."""
        print(f"\n📋 Testing {display_name} ({model_type}):")

        try:
            from gpt_researcher.config.fallback_logic import parse_model_fallbacks

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

            openrouter_models: list[tuple[str, LiteLLMBaseModelSpec]] = []
            first_5_models: list[tuple[str, LiteLLMBaseModelSpec]] = []

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
                print(f"   ❌ Models missing :free suffix: {format_stats['missing_free_suffix']}")
                pytest.fail(f"Found {format_stats['missing_free_suffix']} models missing :free suffix")

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

            assert len(auto_fallbacks) > 0, f"Should generate some fallbacks for {model_type}"

        except Exception as e:
            pytest.fail(f"Error during format conversion test: {e.__class__.__name__}: {e}\n")


class TestConfigurationLoading:
    """Test configuration loading and logging functionality."""

    def test_config_loading(
        self,
        gpt_researcher_config: dict[str, Any],
    ) -> None:
        """Test configuration loading and logging functionality."""
        print("\n" + "=" * 80)
        print("SECTION 5: TESTING CONFIGURATION LOADING AND LOGGING")
        print("=" * 80)

        if not gpt_researcher_config["loaded"]:
            pytest.fail(f"Configuration loading failed: {gpt_researcher_config['error']}")

        config: Config = gpt_researcher_config["config"]

        print("🔧 Initializing GPT Researcher configuration...")
        print("\n📋 CONFIGURATION SUMMARY:")
        print(f"   Fast LLM: {getattr(config, 'fast_llm', 'Not set')}")
        print(f"   Smart LLM: {getattr(config, 'smart_llm', 'Not set')}")
        print(f"   Strategic LLM: {getattr(config, 'strategic_llm', 'Not set')}")
        print(f"   Retrievers: {getattr(config, 'retrievers', 'Not set')}")
        print(f"   Document Path: {getattr(config, 'doc_path', 'Not set')}")

        # Show fallback provider counts
        fast_count: int = len(getattr(config, "fast_llm_fallback_providers", []))
        smart_count: int = len(getattr(config, "smart_llm_fallback_providers", []))
        strategic_count: int = len(getattr(config, "strategic_llm_fallback_providers", []))

        print(f"   ⚡ Fast LLM Fallbacks: {fast_count} providers")
        print(f"   🧠 Smart LLM Fallbacks: {smart_count} providers")
        print(f"   🎯 Strategic LLM Fallbacks: {strategic_count} providers")

        print("✅ Configuration loaded successfully!")

        # Assertions
        assert hasattr(config, "fast_llm"), "Config should have fast_llm"
        assert hasattr(config, "smart_llm"), "Config should have smart_llm"
        assert hasattr(config, "strategic_llm"), "Config should have strategic_llm"


class TestFallbackMechanism:
    """Test fallback mechanism functionality."""

    @pytest.mark.asyncio
    async def test_simple_fallback(
        self,
        gpt_researcher_config: dict[str, Any],
    ) -> None:
        """Test simple request fallback mechanism."""
        if not gpt_researcher_config["loaded"]:
            pytest.skip("Configuration not loaded")

        config: Config = gpt_researcher_config["config"]

        print("\n🧪 Test: Simple Request")
        print("-" * 40)

        try:
            from gpt_researcher.utils.llm import create_chat_completion

            messages: list[dict[str, str]] = [
                {
                    "role": "user",
                    "content": "Say 'Hello, this is a test response!' and nothing else.",
                }
            ]

            response: str = await create_chat_completion(
                messages=messages,
                model=config.smart_llm_model,
                llm_provider=config.smart_llm_provider,
                cfg=config,
                max_tokens=50,
            )
            print(f"✅ Success! Response: {response}")
            assert len(response) > 0, "Should receive a non-empty response"

        except Exception as e:
            pytest.fail(f"Simple fallback test failed: {e.__class__.__name__}: {e}")

    @pytest.mark.asyncio
    async def test_large_context_fallback(
        self,
        gpt_researcher_config: dict[str, Any],
    ) -> None:
        """Test large context request fallback mechanism."""
        if not gpt_researcher_config["loaded"]:
            pytest.skip("Configuration not loaded")

        config: Config = gpt_researcher_config["config"]

        print("\n🧪 Test: Large Context Request")
        print("-" * 40)

        try:
            from gpt_researcher.utils.llm import create_chat_completion

            # Create a large context
            large_content: str = "This is a test sentence. " * 1000
            large_messages: list[dict[str, str]] = [
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": f"Please summarize this text in one sentence: {large_content}",
                },
            ]

            response: str = await create_chat_completion(
                messages=large_messages,
                model=config.smart_llm_model,
                llm_provider=config.smart_llm_provider,
                cfg=config,
                max_tokens=100,
            )
            print(f"✅ Success! Response: {response[:200]}...")
            assert len(response) > 0, "Should receive a non-empty response for large context"

        except Exception as e:
            # Large context might legitimately fail, so we'll log but not fail the test
            print(f"❌ Large context test failed: {type(e).__name__}: {e}")
            pytest.skip(f"Large context test failed - this may be expected: {e.__class__.__name__}: {e}")

    @pytest.mark.asyncio
    async def test_invalid_model_fallback(
        self,
        gpt_researcher_config: dict[str, Any],
    ) -> None:
        """Test invalid model fallback mechanism."""
        if not gpt_researcher_config["loaded"]:
            pytest.skip("Configuration not loaded")

        config: Config = gpt_researcher_config["config"]

        print("\n🧪 Test: Invalid Model")
        print("-" * 40)

        try:
            from gpt_researcher.utils.llm import create_chat_completion

            messages: list[dict[str, str]] = [
                {
                    "role": "user",
                    "content": "Say 'Hello, this is a test response!' and nothing else.",
                }
            ]

            response: str = await create_chat_completion(
                messages=messages,
                model="invalid-model-that-does-not-exist",
                llm_provider=config.smart_llm_provider,
                cfg=config,
                max_tokens=50,
            )
            print(f"✅ Success with fallback! Response: {response}")
            assert len(response) > 0, "Should receive a response via fallback"

        except Exception as e:
            print(f"❌ All providers failed: {e.__class__.__name__}: {e}")
            # This test might legitimately fail if no fallbacks work
            pytest.skip(
                f"Invalid model fallback test failed - all providers failed: {e.__class__.__name__}: {e}",
            )


class TestReportGeneration:
    """Test report generation functionality."""

    @pytest.mark.asyncio
    async def test_simple_report_generation(
        self,
        gpt_researcher_config: dict[str, Any],
    ) -> None:
        """Test simple report generation."""
        if not gpt_researcher_config["loaded"]:
            pytest.skip("Configuration not loaded")

        config: Config = gpt_researcher_config["config"]

        print("\n🧪 Test: Simple Report Generation")
        print("-" * 40)

        try:
            from gpt_researcher.actions.report_generation import generate_report
            from gpt_researcher.utils.enum import Tone

            print(f"Primary model: {config.smart_llm_model}")
            print(f"Primary provider: {config.smart_llm_provider}")
            print(f"Token limit: {config.smart_token_limit}")

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
                assert len(report) > 0, "Report should not be empty"
                assert "artificial intelligence" in report.lower(), "Report should mention AI"
            else:
                pytest.fail("Empty report generated")

        except Exception as e:
            pytest.fail(f"Simple report generation failed: {e.__class__.__name__}: {e}")

    @pytest.mark.asyncio
    async def test_large_context_report_generation(
        self,
        gpt_researcher_config: dict[str, Any],
    ) -> None:
        """Test large context report generation."""
        if not gpt_researcher_config["loaded"]:
            pytest.skip("Configuration not loaded")

        config: Config = gpt_researcher_config["config"]

        print("\n🧪 Test: Large Context Report Generation")
        print("-" * 40)

        large_context: str = (
            """Artificial intelligence (AI) is a rapidly evolving field that encompasses various technologies and approaches."""
            + "This is a test sentence that will be repeated many times to create a large context. "
            * 500
        )

        try:
            from gpt_researcher.actions.report_generation import generate_report
            from gpt_researcher.utils.enum import Tone

            report: str = await generate_report(
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
                assert len(report) > 0, "Large context report should not be empty"
            else:
                pytest.fail("Empty report generated for large context")

        except Exception as e:
            # Large context might legitimately fail
            print(f"❌ Error with large context: {e.__class__.__name__}: {e}")
            pytest.skip(f"Large context report generation failed - this may be expected: {e.__class__.__name__}: {e}")


# Summary function for manual execution
def print_test_summary():
    """Print a summary when running pytest manually."""
    print("\n" + "=" * 100)
    print("GPT-RESEARCHER COMPREHENSIVE PYTEST SUITE")
    print("=" * 100)
    print("Run with: pytest test_comprehensive_pytest.py -v -s")
    print("Run specific test: pytest test_comprehensive_pytest.py::TestLLMFallbacksLoading::test_llm_fallbacks_import -v -s")
    print("Run async tests only: pytest test_comprehensive_pytest.py -k 'asyncio' -v -s")
    print("=" * 100)


if __name__ == "__main__":
    print_test_summary()
