import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    ("module_name", "class_name"),
    [
        ("gpt_researcher.retrievers.arxiv.arxiv", "ArxivSearch"),
        (
            "gpt_researcher.retrievers.semantic_scholar.semantic_scholar",
            "SemanticScholarSearch",
        ),
        ("gpt_researcher.retrievers.openalex.openalex", "OpenAlexSearch"),
    ],
)
def test_invalid_sort_rejected_under_optimized_python(module_name, class_name):
    script = f"""
import builtins
import importlib
import typing

builtins.Any = typing.Any
builtins.List = typing.List
search_class = getattr(importlib.import_module({module_name!r}), {class_name!r})

try:
    search_class("query", sort="invalid")
except ValueError:
    pass
else:
    raise SystemExit("invalid sort was accepted")
"""

    result = subprocess.run(
        [sys.executable, "-O", "-c", script],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
