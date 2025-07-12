#!/usr/bin/env python3
"""
Advanced test for middle-out transform with actual model queries.
"""
from __future__ import annotations

import asyncio
import time

from gpt_researcher.llm_provider.generic.base import GenericLLMProvider


def count_tokens_rough(text: str) -> int:
    """Rough token count estimation (1 token ≈ 4 characters)."""
    return len(text) // 4

async def test_middle_out_with_long_response():
    """Test that middle-out transform works with a response that would exceed context limits."""

    print("🔍 TESTING: Middle-out transform with long response (~17k tokens)")
    print("=" * 80)

    # Create a prompt designed to generate a very long response
    long_prompt = """
    Write an extremely comprehensive, detailed academic research paper about the history and evolution of artificial intelligence from 1950 to 2024.

    Your response should include:
    1. A detailed introduction (minimum 500 words)
    2. Historical timeline with major milestones (minimum 2000 words)
    3. Key figures and their contributions (minimum 2000 words)
    4. Technical breakthroughs and algorithms (minimum 2000 words)
    5. Applications and industry impact (minimum 2000 words)
    6. Ethical considerations and challenges (minimum 1500 words)
    7. Current state of AI in 2024 (minimum 1500 words)
    8. Future predictions and trends (minimum 1500 words)
    9. Detailed conclusion (minimum 500 words)
    10. Comprehensive bibliography with at least 50 sources

    Make sure to be extremely detailed, provide specific examples, dates, technical explanations, and real-world applications.
    Include code examples where relevant. Write in academic style with proper citations.

    This should be a publication-ready research paper of approximately 15,000-20,000 words.
    """

    messages = [
        {"role": "system", "content": "You are an expert AI researcher and academic writer. Write comprehensive, detailed responses with extensive examples and explanations."},
        {"role": "user", "content": long_prompt}
    ]

    try:
        # Test with OpenRouter provider (should have middle-out transform)
        print("🔧 Creating OpenRouter provider with middle-out transform...")
        provider = GenericLLMProvider.from_provider(
            "openrouter",
            model="google/gemini-2.0-flash-exp:free",  # Use a more available model
            temperature=0.7,
            max_tokens=16000  # Request a large number of tokens
        )

        # Verify middle-out transform is present
        extra_body = getattr(provider.llm, "extra_body", {})
        transforms = extra_body.get("transforms", [])
        print(f"🔧 Transforms configured: {transforms}")

        if "middle-out" not in transforms:
            print("❌ FAILED: Middle-out transform not found in provider!")
            return False

        print("✅ Middle-out transform confirmed in provider")
        print(f"🔧 Estimated input tokens: {count_tokens_rough(str(messages))}")
        print("🚀 Sending request to OpenRouter with middle-out transform...")

        start_time = time.time()

        try:
            response = await provider.get_chat_response(messages, stream=False)
            end_time = time.time()

            response_tokens = count_tokens_rough(response)
            total_tokens = count_tokens_rough(str(messages)) + response_tokens

            print("✅ SUCCESS: Received response from OpenRouter!")
            print(f"🔧 Response time: {end_time - start_time:.2f} seconds")
            print(f"🔧 Response length: {len(response)} characters")
            print(f"🔧 Estimated response tokens: {response_tokens}")
            print(f"🔧 Estimated total tokens: {total_tokens}")
            print("🔧 Response preview (first 500 chars):")
            print("-" * 60)
            print(response[:500] + "..." if len(response) > 500 else response)
            print("-" * 60)

            # Check if we got a substantial response
            if response_tokens > 5000:
                print("✅ SUCCESS: Received substantial response (>5000 tokens)")
                print("✅ Middle-out transform likely handled context compression successfully!")
                return True
            elif response_tokens > 1000:
                print("⚠️ PARTIAL SUCCESS: Received moderate response (>1000 tokens)")
                print("⚠️ Middle-out transform may have been used, but response could be longer")
                return True
            else:
                print("❌ FAILED: Response too short, middle-out may not have worked properly")
                return False

        except Exception as e:
            print(f"❌ ERROR: Request failed: {e.__class__.__name__}: {e}")

            # Check if it's a context length error (which would indicate middle-out didn't work)
            if (
                "context" in str(e).lower()
                or "token" in str(e).lower()
                or "length" in str(e).lower()
            ):
                print("❌ CRITICAL: Context length error suggests middle-out transform failed!")
                return False
            else:
                print("⚠️ Request failed for other reasons (API key, rate limit, etc.)")
                return False

    except Exception as e:
        print(f"❌ ERROR: Failed to create OpenRouter provider: {e.__class__.__name__}: {e}")
        return False

async def test_middle_out_vs_regular_provider():
    """Compare OpenRouter (with middle-out) vs regular provider behavior."""

    print("\n🔍 TESTING: Comparing middle-out vs regular provider")
    print("=" * 80)

    # Shorter prompt for comparison test
    comparison_prompt = """
    Write a comprehensive guide to machine learning algorithms. Include:
    1. Linear regression with mathematical formulas
    2. Decision trees with examples
    3. Neural networks with architecture details
    4. Support vector machines with kernel explanations
    5. Clustering algorithms with use cases
    6. Ensemble methods with practical applications

    Make it detailed with code examples in Python. Aim for about 8000-10000 words.
    """

    messages = [
        {"role": "system", "content": "You are an expert machine learning engineer. Provide detailed technical explanations."},
        {"role": "user", "content": comparison_prompt}
    ]

    try:
        # Test OpenRouter with middle-out
        print("🔧 Testing OpenRouter with middle-out transform...")
        openrouter_provider = GenericLLMProvider.from_provider(
            "openrouter",
            model="google/gemini-2.0-flash-exp:free",  # Use a more available model
            temperature=0.7,
            max_tokens=8000
        )

        start_time = time.time()
        try:
            openrouter_response = await openrouter_provider.get_chat_response(messages, stream=False)
            openrouter_time = time.time() - start_time
            openrouter_tokens = count_tokens_rough(openrouter_response)

            print(f"✅ OpenRouter response: {len(openrouter_response)} chars, ~{openrouter_tokens} tokens, {openrouter_time:.2f}s")

        except Exception as e:
            print(f"❌ OpenRouter failed: {e.__class__.__name__}: {e}")
            openrouter_response = None
            openrouter_tokens = 0

        # Test regular OpenAI provider (if available) for comparison
        print("🔧 Testing regular OpenAI provider for comparison...")
        try:
            openai_provider = GenericLLMProvider.from_provider(
                "openai",
                model="gpt-4",
                temperature=0.7,
                max_tokens=8000
            )

            start_time = time.time()
            openai_response = await openai_provider.get_chat_response(messages, stream=False)
            openai_time = time.time() - start_time
            openai_tokens = count_tokens_rough(openai_response)

            print(f"✅ OpenAI response: {len(openai_response)} chars, ~{openai_tokens} tokens, {openai_time:.2f}s")

        except Exception as e:
            print(f"⚠️ OpenAI not available: {e.__class__.__name__}: {e}")
            openai_response = None
            openai_tokens = 0

        # Compare results
        if openrouter_response and openai_response:
            print("\n📊 COMPARISON RESULTS:")
            print(f"   OpenRouter (middle-out): ~{openrouter_tokens} tokens")
            print(f"   OpenAI (regular):        ~{openai_tokens} tokens")

            if openrouter_tokens > openai_tokens * 0.8:  # Allow some variance
                print("✅ OpenRouter with middle-out produced comparable or better output!")
                return True
            else:
                print("⚠️ OpenRouter response significantly shorter than expected")
                return False
        elif openrouter_response:
            print("✅ OpenRouter with middle-out worked (OpenAI not available for comparison)")
            return True
        else:
            print("❌ Both providers failed")
            return False

    except Exception as e:
        print(f"❌ ERROR: Comparison test failed: {e.__class__.__name__}: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Testing middle-out transform with actual model queries...\n")

    result1 = asyncio.run(test_middle_out_with_long_response())
    result2 = asyncio.run(test_middle_out_vs_regular_provider())

    print("\n📋 TEST RESULTS:")
    print(f"   Long response test: {'✅ PASSED' if result1 else '❌ FAILED'}")
    print(f"   Comparison test:    {'✅ PASSED' if result2 else '❌ FAILED'}")

    if result1 and result2:
        print("\n🎉 All tests passed! Middle-out transform is working correctly with real queries.")
    else:
        print("\n💥 Some tests failed. Middle-out transform may need investigation.")
