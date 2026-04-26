import urllib.parse

import pytest

from backend.server import app as server_app
from gpt_researcher.research_run_store import ResearchRunStore


def test_resolve_output_artifact_path_accepts_encoded_absolute_output_path(tmp_path, monkeypatch):
    monkeypatch.setattr(server_app, "OUTPUTS_DIR", tmp_path.resolve())
    artifact = tmp_path / "research_task.docx"
    artifact.write_bytes(b"docx")

    encoded = urllib.parse.quote(str(artifact))

    assert server_app.resolve_output_artifact_path(encoded, expected_suffix="docx") == artifact


def test_resolve_output_artifact_path_accepts_relative_output_path(tmp_path, monkeypatch):
    monkeypatch.setattr(server_app, "OUTPUTS_DIR", tmp_path.resolve())
    artifact = tmp_path / "nested" / "research_task.md"
    artifact.parent.mkdir()
    artifact.write_text("# Report", encoding="utf-8")

    assert (
        server_app.resolve_output_artifact_path("outputs/nested/research_task.md", expected_suffix="md")
        == artifact
    )


@pytest.mark.parametrize(
    ("path_value", "expected_suffix"),
    [
        ("/app/outputs/../secret.docx", "docx"),
        ("outputs/report.pdf", "docx"),
    ],
)
def test_resolve_output_artifact_path_rejects_unsafe_or_wrong_extension(
    tmp_path,
    monkeypatch,
    path_value,
    expected_suffix,
):
    monkeypatch.setattr(server_app, "OUTPUTS_DIR", tmp_path.resolve())

    assert server_app.resolve_output_artifact_path(path_value, expected_suffix=expected_suffix) is None


def test_resolve_report_docx_path_prefers_run_store_docx_path(tmp_path, monkeypatch):
    monkeypatch.setattr(server_app, "OUTPUTS_DIR", tmp_path.resolve())
    store = ResearchRunStore(tmp_path / "runs.sqlite3")
    monkeypatch.setattr(server_app, "research_run_store", store)

    artifact = tmp_path / "top_trends_report.docx"
    artifact.write_bytes(b"docx")
    store.create_run("research_123", query="top trends")
    store.complete_run("research_123", docx_path=urllib.parse.quote(str(artifact)))

    assert server_app.resolve_report_docx_path("research_123") == artifact


def test_resolve_report_docx_path_rejects_traversal_ids():
    with pytest.raises(server_app.HTTPException):
        server_app.resolve_report_docx_path("../research_123")
