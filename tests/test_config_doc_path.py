"""Document configuration must retain environment overrides."""

import json

import pytest

from gpt_researcher.config.config import Config


@pytest.fixture
def config_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("REPORT_SOURCE", raising=False)
    monkeypatch.delenv("DOC_PATH", raising=False)
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "REPORT_SOURCE": "local",
        "DOC_PATH": str(tmp_path / "from-file"),
    }))
    return path


def test_doc_path_environment_overrides_file(config_file, tmp_path, monkeypatch):
    document_dir = tmp_path / "from-env"
    monkeypatch.setenv("DOC_PATH", str(document_dir))

    config = Config(str(config_file))

    assert config.doc_path == str(document_dir)
    assert document_dir.is_dir()
    assert not (tmp_path / "from-file").exists()


def test_doc_path_from_file_without_override(config_file, tmp_path):
    config = Config(str(config_file))

    assert config.doc_path == str(tmp_path / "from-file")
    assert (tmp_path / "from-file").is_dir()


@pytest.mark.parametrize("report_source", ["local", "web"])
def test_document_setup_uses_effective_report_source(
    config_file, tmp_path, monkeypatch, report_source
):
    config_file.write_text(json.dumps({
        "REPORT_SOURCE": "web" if report_source == "local" else "local",
        "DOC_PATH": str(tmp_path / "documents"),
    }))
    monkeypatch.setenv("REPORT_SOURCE", report_source)

    config = Config(str(config_file))

    assert config.report_source == report_source
    assert (tmp_path / "documents").is_dir() == (report_source == "local")
