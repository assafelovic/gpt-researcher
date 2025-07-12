#!/usr/bin/env python3
"""
Test script to demonstrate the improved logging in GPT Researcher config.
This shows how the new logging will look compared to the old verbose output.
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_improved_logging():
    """Test the improved logging functionality."""
    print("=" * 80)
    print("GPT RESEARCHER - IMPROVED CONFIG LOGGING DEMO")
    print("=" * 80)
    print()

    try:
        from gpt_researcher.config.config import Config

        # Test with default config (should show improved logging)
        print("🔧 Initializing GPT Researcher configuration...")
        print()

        config = Config()

        print()
        print("=" * 80)
        print("CONFIGURATION SUMMARY")
        print("=" * 80)
        print(f"📋 Fast LLM: {getattr(config, 'fast_llm', 'Not set')}")
        print(f"🧠 Smart LLM: {getattr(config, 'smart_llm', 'Not set')}")
        print(f"🎯 Strategic LLM: {getattr(config, 'strategic_llm', 'Not set')}")
        print(f"🔍 Retrievers: {getattr(config, 'retrievers', 'Not set')}")
        print(f"📁 Document Path: {getattr(config, 'doc_path', 'Not set')}")

        # Show fallback provider counts
        fast_count = len(getattr(config, 'fast_llm_fallback_providers', []))
        smart_count = len(getattr(config, 'smart_llm_fallback_providers', []))
        strategic_count = len(getattr(config, 'strategic_llm_fallback_providers', []))

        print(f"⚡ Fast LLM Fallbacks: {fast_count} providers")
        print(f"🧠 Smart LLM Fallbacks: {smart_count} providers")
        print(f"🎯 Strategic LLM Fallbacks: {strategic_count} providers")
        print()

        print("✅ Configuration loaded successfully!")
        print("📝 Check the logs above to see the improved, structured logging format.")

    except Exception as e:
        print(f"❌ Error during configuration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_logging()
