#!/usr/bin/env python3
"""Test script to verify fallback mechanism is working correctly."""
from __future__ import annotations

import asyncio
import logging

from gpt_researcher.config.config import Config
from gpt_researcher.utils.llm import create_chat_completion

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


async def test_fallback_mechanism():
    """Test the fallback mechanism with various scenarios."""
    print("=" * 80)
    print("TESTING FALLBACK MECHANISM")
    print("=" * 80)

    # Load configuration
    cfg = Config()

    print("\n📋 Configuration Summary:")
    print(f"   Smart LLM: {cfg.smart_llm}")
    print(f"   Smart LLM Provider: {cfg.smart_llm_provider}")
    print(f"   Smart LLM Model: {cfg.smart_llm_model}")
    print(f"   Available Fallback Providers: {len(cfg.smart_llm_fallback_providers)}")

    if cfg.smart_llm_fallback_providers:
        print("   Fallback Models:")
        for i, provider in enumerate(cfg.smart_llm_fallback_providers):
            model_name: str = getattr(provider.llm, "model_name", None) or getattr(provider.llm, "model", "unknown")
            print(f"     {i+1}. {model_name}")
    else:
        print("   ⚠️  No fallback providers configured!")
        return

    print("\n🧪 Test 1: Simple Request (should work with primary or fallback)")
    print("-" * 60)

    messages: list[dict[str, str]] = [{"role": "user", "content": "Say 'Hello, this is a test response!' and nothing else."}]

    try:
        response: str = await create_chat_completion(
            messages=messages,
            model=cfg.smart_llm_model,
            llm_provider=cfg.smart_llm_provider,
            cfg=cfg,
            max_tokens=50,  # Small limit to test
        )
        print(f"✅ Success! Response: {response}")

    except Exception as e:
        print(f"❌ Failed: {e.__class__.__name__}: {e}")

    print("\n🧪 Test 2: Large Context Request (should trigger token handling)")
    print("-" * 60)

    # Create a large context that might trigger token limits
    large_content: str = "This is a test sentence. " * 1000  # Repeat to create large content
    large_messages: list[dict[str, str]] = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Please summarize this text in one sentence: {large_content}"},
    ]

    try:
        response: str = await create_chat_completion(messages=large_messages, model=cfg.smart_llm_model, llm_provider=cfg.smart_llm_provider, cfg=cfg, max_tokens=100)
        print(f"✅ Success! Response: {response[:200]}...")

    except Exception as e:
        print(f"❌ Failed: {e.__class__.__name__}: {e}")

    print("\n🧪 Test 3: Invalid Model (should trigger fallback)")
    print("-" * 60)

    try:
        response: str = await create_chat_completion(messages=messages, model="invalid-model-that-does-not-exist", llm_provider=cfg.smart_llm_provider, cfg=cfg, max_tokens=50)
        print(f"✅ Success with fallback! Response: {response}")

    except Exception as e:
        print(f"❌ All providers failed: {e.__class__.__name__}: {e}")

    print("\n" + "=" * 80)
    print("FALLBACK MECHANISM TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_fallback_mechanism())
