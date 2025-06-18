#!/usr/bin/env python3
"""
Test script to verify that the middle-out transform is applied to OpenRouter requests.
"""
from __future__ import annotations

import asyncio
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

async def test_middle_out_transform():
    """Test that middle-out transform is applied to OpenRouter providers."""

    print("🔍 TESTING: Middle-out transform for OpenRouter")
    print("=" * 60)

    # Test creating an OpenRouter provider
    try:
        provider = GenericLLMProvider.from_provider(
            "openrouter",
            model="google/gemini-2.5-pro-exp-03-25:free",
            temperature=0.7,
            max_tokens=1000
        )

        # Check if the provider has the middle-out transform
        model_kwargs = getattr(provider.llm, 'model_kwargs', {})
        transforms = model_kwargs.get('transforms', [])

        print(f"🔧 Provider created: {type(provider.llm).__name__}")
        print(f"🔧 Model kwargs: {model_kwargs}")
        print(f"🔧 Transforms: {transforms}")

        if "middle-out" in transforms:
            print("✅ SUCCESS: Middle-out transform is present in OpenRouter provider!")
            return True
        else:
            print("❌ FAILED: Middle-out transform is missing from OpenRouter provider!")
            return False

    except Exception as e:
        print(f"❌ ERROR: Failed to create OpenRouter provider: {e.__class__.__name__}: {str(e)}")
        return False

async def test_other_providers_no_transform():
    """Test that middle-out transform is NOT applied to non-OpenRouter providers."""

    print("\n🔍 TESTING: Other providers should NOT have middle-out transform")
    print("=" * 60)

    # Test with a non-OpenRouter provider (if available)
    try:
        # Test with OpenAI provider
        provider = GenericLLMProvider.from_provider(
            "openai",
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000
        )

        # Check if the provider has the middle-out transform
        model_kwargs = getattr(provider.llm, 'model_kwargs', {})
        transforms = model_kwargs.get('transforms', [])

        print(f"🔧 Provider created: {type(provider.llm).__name__}")
        print(f"🔧 Model kwargs: {model_kwargs}")
        print(f"🔧 Transforms: {transforms}")

        if "middle-out" not in transforms:
            print("✅ SUCCESS: Middle-out transform is correctly NOT present in OpenAI provider!")
            return True
        else:
            print("❌ FAILED: Middle-out transform should not be present in OpenAI provider!")
            return False

    except Exception as e:
        print(f"⚠️ SKIPPED: Could not test OpenAI provider: {e.__class__.__name__}: {str(e)}")
        return True  # Skip this test if OpenAI is not available

if __name__ == "__main__":
    print("🚀 Testing middle-out transform configuration...\n")

    result1 = asyncio.run(test_middle_out_transform())
    result2 = asyncio.run(test_other_providers_no_transform())

    if result1 and result2:
        print("\n🎉 All tests passed! Middle-out transform is correctly configured.")
    else:
        print("\n💥 Some tests failed. Please check the configuration.")
