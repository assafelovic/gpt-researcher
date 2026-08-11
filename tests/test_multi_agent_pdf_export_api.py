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


@pytest.mark.parametrize("api_version", ["legacy", "current"])
@pytest.mark.asyncio
async def test_pdf_export_supports_md2pdf_api_versions(
    api_version,
    tmp_path,
    monkeypatch,
):
    captured = {}

    if api_version == "current":

        def fake_md2pdf(pdf, raw=None, md=None, css=None, base_url=None):
            captured.update(
                pdf=pdf,
                content=raw,
                markdown_file=md,
                css=css,
                base_url=base_url,
            )
            Path(pdf).write_bytes(b"pdf")

    else:

        def fake_md2pdf(
            pdf_file_path,
            md_content=None,
            md_file_path=None,
            css_file_path=None,
            base_url=None,
        ):
            captured.update(
                pdf=pdf_file_path,
                content=md_content,
                markdown_file=md_file_path,
                css=css_file_path,
                base_url=base_url,
            )
            Path(pdf_file_path).write_bytes(b"pdf")

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
    assert captured["content"] == "# Report"
    assert captured["markdown_file"] is None
    assert Path(captured["css"]).name == "pdf_styles.css"
    assert captured["base_url"] is None
