#!/usr/bin/env python3
"""Launcher script for the GPT Researcher Toga frontend."""

from __future__ import annotations

import sys

from pathlib import Path

if __name__ == "__main__":
    absolute_file_path = Path(__file__).absolute()
    if str(absolute_file_path) not in sys.path:
        sys.path.append(str(absolute_file_path))
    from standalone_app.app import main

    app = main()
    app.main_loop()
