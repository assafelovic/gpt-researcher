import json
from pathlib import Path


def test_unique_artifact_stems_are_distinct():
    from gpt_researcher.utils.artifacts import make_unique_artifact_stem

    first = make_unique_artifact_stem("task", "same label")
    second = make_unique_artifact_stem("task", "same label")

    assert first != second
    assert first.startswith("task_")
    assert second.startswith("task_")


def test_research_logging_setup_uses_outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    from backend.server.logging_config import get_json_handler, setup_research_logging

    first_log_file, first_json_file, _, _ = setup_research_logging()
    second_log_file, second_json_file, research_logger, json_handler = setup_research_logging()

    first_log_path = Path(first_log_file)
    first_json_path = Path(first_json_file)
    second_log_path = Path(second_log_file)
    second_json_path = Path(second_json_file)

    assert first_log_path != second_log_path
    assert first_json_path != second_json_path
    assert first_log_path.parent.name == "outputs"
    assert first_json_path.parent.name == "outputs"
    assert second_log_path.parent.name == "outputs"
    assert second_json_path.parent.name == "outputs"
    assert first_log_path.exists()
    assert first_json_path.exists()
    assert second_log_path.exists()
    assert second_json_path.exists()
    assert get_json_handler() is json_handler
    assert research_logger.output_dir == "outputs"

    json_handler.log_event("logs", {"message": "Test log entry"})
    json_handler.update_content("query", "test query")

    with second_json_path.open() as f:
        data = json.load(f)

    assert data["events"]
    assert data["events"][0]["type"] == "logs"
    assert data["content"]["query"] == "test query"

    for handler in list(research_logger.handlers):
        handler.close()
        research_logger.removeHandler(handler)

    for artifact_path in (
        first_log_path,
        first_json_path,
        second_log_path,
        second_json_path,
    ):
        if artifact_path.exists():
            artifact_path.unlink()
