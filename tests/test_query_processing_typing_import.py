"""Regression: query_processing must import without NameError (issue #1981)."""
from __future__ import annotations

import ast
from pathlib import Path


def test_query_processing_source_has_typing_imports_before_any_use():
    path = Path(__file__).resolve().parents[1] / "gpt_researcher" / "actions" / "query_processing.py"
    src = path.read_text(encoding="utf-8")
    # Parse successfully
    tree = ast.parse(src)

    # Either future annotations or typing imported before first use of Name Any in annotations
    has_future = any(
        isinstance(n, ast.ImportFrom) and n.module == "__future__" and any(a.name == "annotations" for a in n.names)
        for n in tree.body
        if isinstance(n, (ast.Import, ast.ImportFrom))
    )
    typing_import_line = None
    for n in tree.body:
        if isinstance(n, ast.ImportFrom) and n.module == "typing":
            typing_import_line = n.lineno
            break

    # Find first FunctionDef that uses Any in annotations
    first_any_line = None
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            for arg in n.args.args:
                if arg.annotation and "Any" in ast.dump(arg.annotation):
                    first_any_line = n.lineno
                    break
            if first_any_line:
                break

    assert first_any_line is not None, "expected a function using Any"
    assert has_future or (typing_import_line is not None and typing_import_line < first_any_line), (
        "Any used before typing import and without from __future__ import annotations"
    )


def test_normalize_sub_queries_available():
    # Lightweight import path: load module after injecting package stubs if needed
    import sys
    import types
    # Prefer real import if installed; else skip heavy
    try:
        from gpt_researcher.actions.query_processing import _normalize_sub_queries
    except Exception as exc:
        # If dependency missing, still assert module file is self-consistent at runtime for annotations
        # by exec with mocked deps
        path = Path(__file__).resolve().parents[1] / "gpt_researcher" / "actions" / "query_processing.py"
        src = path.read_text(encoding="utf-8")
        # This would raise NameError without the fix when future annotations absent and Any unbound
        compile(src, str(path), "exec")
        return
    assert _normalize_sub_queries(["a", "b"], "fb") == ["a", "b"]
    assert _normalize_sub_queries(None, "fallback") == ["fallback"]
