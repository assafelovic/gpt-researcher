#!/usr/bin/env python3
"""Seed Hermes memory directory with estate canon if empty."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

HERMES_HOME = Path(os.getenv("HERMES_HOME", "/data/hermes"))
SEED_DIR = Path(__file__).resolve().parent / "seed"
MEMORY_DIR = HERMES_HOME / "memory"


def main() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    for src in SEED_DIR.glob("*.md"):
        dest = MEMORY_DIR / src.name
        if not dest.exists():
            shutil.copy2(src, dest)
            print(f"[hermes] seeded {dest}")
        else:
            print(f"[hermes] keep existing {dest}")


if __name__ == "__main__":
    main()
