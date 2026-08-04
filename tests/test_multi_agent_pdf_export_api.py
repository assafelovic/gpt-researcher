import importlib.util
import sys
import types
import urllib.parse
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "multi_agents"
    / "agents"
    / "utils"
    / "file_formats.py"
)
SPEC = importlib.util.spec_from_file_location("multi_agent_file_formats", MODULE_PATH)
file_formats = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(file_formats)


@pytest.mark.asyncio
async def test_pdf_export_uses_current_md2pdf_api(tmp_path, monkeypatch):
    captured = {}

    def fake_md2pdf(pdf, raw=None, md=None, css=None, base_url=None):
        captured.update(
            {
                "pdf": pdf,
                "raw": raw,
                "md": md,
                "css": css,
                "base_url": base_url,
            }
        )
        Path(pdf).write_bytes(b"pdf")

    core_module = types.ModuleType("md2pdf.core")
    core_module.md2pdf = fake_md2pdf
    package_module = types.ModuleType("md2pdf")
    package_module.core = core_module
    monkeypatch.setitem(sys.modules, "md2pdf", package_module)
    monkeypatch.setitem(sys.modules, "md2pdf.core", core_module)

    result = await file_formats.write_md_to_pdf("# Report", str(tmp_path))

    assert result
    output_path = Path(urllib.parse.unquote(result))
    assert output_path.exists()
    assert captured["raw"] == "# Report"
    assert captured["md"] is None
    assert Path(captured["css"]).name == "pdf_styles.css"
    assert captured["base_url"] is None
