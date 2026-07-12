"""Filename/directory hygiene for report PDF export (#1718)."""

import asyncio
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from backend import utils as backend_utils


@pytest.mark.asyncio
async def test_empty_filename_does_not_write_dot_pdf(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def fake_md2pdf(file_path, raw=None, css=None, base_url=None):
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        Path(file_path).write_text("pdf-bytes", encoding="utf-8")

    with patch.dict("sys.modules", {}):
        with patch("md2pdf.core.md2pdf", create=True, side_effect=fake_md2pdf):
            # Import path used inside function: from md2pdf.core import md2pdf
            import sys
            import types
            core = types.ModuleType("md2pdf.core")
            core.md2pdf = fake_md2pdf
            md2pdf_mod = types.ModuleType("md2pdf")
            md2pdf_mod.core = core
            sys.modules["md2pdf"] = md2pdf_mod
            sys.modules["md2pdf.core"] = core

            path = await backend_utils.write_md_to_pdf("# hi", filename="")

    assert path
    decoded = path.replace("%2F", "/")
    assert not decoded.endswith("/.pdf")
    assert decoded.startswith("outputs/")
    assert Path(tmp_path / decoded).exists()


@pytest.mark.asyncio
async def test_explicit_filename_preserved(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import sys, types

    def fake_md2pdf(file_path, raw=None, css=None, base_url=None):
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        Path(file_path).write_text("pdf", encoding="utf-8")

    core = types.ModuleType("md2pdf.core")
    core.md2pdf = fake_md2pdf
    md2pdf_mod = types.ModuleType("md2pdf")
    md2pdf_mod.core = core
    sys.modules["md2pdf"] = md2pdf_mod
    sys.modules["md2pdf.core"] = core

    path = await backend_utils.write_md_to_pdf("# hi", filename="my-report")
    assert "my-report.pdf" in path
    assert (tmp_path / "outputs" / "my-report.pdf").exists()
