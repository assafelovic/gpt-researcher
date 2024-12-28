#!/usr/bin/env python3
"""Launcher script for the GPT Researcher Toga frontend."""
from __future__ import annotations

from toga_frontend.app import main

if __name__ == "__main__":
    app = main()
    app.main_loop()