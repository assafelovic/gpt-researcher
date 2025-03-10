#!/usr/bin/env python
"""
Deep Research Runner Script

This script provides a simple way to run the deep research module directly.
"""

import asyncio
import sys
import os

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from multi_agents.deep_research.main import main

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main()) 