#!/usr/bin/env python3
"""Test script to demonstrate enhanced FREE_MODELS logging."""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, '.')

# Set environment variables for testing
os.environ['FAST_LLM'] = 'auto'
os.environ['SMART_LLM'] = 'auto'
os.environ['STRATEGIC_LLM'] = 'auto'

# Import and create config
from gpt_researcher.config.config import Config

print("=" * 80)
print("TESTING ENHANCED FREE_MODELS LOGGING")
print("=" * 80)

try:
    config = Config()
    print("\n" + "=" * 80)
    print("Configuration loaded successfully!")
    print("=" * 80)
except Exception as e:
    print(f"Error loading config: {e}")
    import traceback
    traceback.print_exc()
