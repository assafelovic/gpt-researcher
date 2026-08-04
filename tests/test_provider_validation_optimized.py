import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("method_name", ["parse_llm", "parse_embedding"])
def test_provider_validation_survives_optimized_python(method_name):
    project_root = Path(__file__).resolve().parents[1]
    script = f"""
import builtins
import typing

builtins.Any = typing.Any
builtins.List = typing.List

from gpt_researcher.config.config import Config

try:
    Config.{method_name}("unsupported-provider:model")
except ValueError:
    pass
else:
    raise SystemExit("unsupported provider was accepted")
"""

    result = subprocess.run(
        [sys.executable, "-O", "-c", script],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
