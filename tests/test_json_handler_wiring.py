"""setup_research_logging() must publish its JSON handler where get_json_handler()
looks it up, otherwise the structured research log records nothing."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

path = (
    Path(__file__).resolve().parents[1]
    / "gpt_researcher"
    / "utils"
    / "logging_config.py"
)
spec = importlib.util.spec_from_file_location("gptr_logging_config_ut", path)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def _cleanup(logger) -> None:
    for handler in list(logger.handlers):
        handler.close()
    logger.handlers.clear()
    if hasattr(logger, "json_handler"):
        del logger.json_handler
    sys.modules.pop(spec.name, None)


def test_get_json_handler_returns_the_handler_setup_created(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_file, json_file, logger, json_handler = mod.setup_research_logging()
    try:
        assert Path(log_file).exists()

        # ResearchConductor stores whatever this returns and skips every JSON log
        # entry when it is None.
        assert mod.get_json_handler() is json_handler

        mod.get_json_handler().update_content("query", "solid-state batteries")
        saved = json.loads(Path(json_file).read_text(encoding="utf-8"))
        assert saved["content"]["query"] == "solid-state batteries"
    finally:
        _cleanup(logger)
