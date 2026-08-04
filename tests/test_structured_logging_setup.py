import logging

import pytest

from gpt_researcher.utils.logging_config import (
    get_json_handler,
    setup_research_logging,
)


@pytest.fixture(autouse=True)
def cleanup_research_logger():
    yield
    logger = logging.getLogger("research")
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    if hasattr(logger, "json_handler"):
        del logger.json_handler


def test_setup_registers_json_handler_for_research_conductor(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    _, _, logger, json_handler = setup_research_logging()

    assert get_json_handler() is json_handler
    assert logger.json_handler is json_handler


def test_setup_closes_replaced_file_handlers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    _, _, logger, _ = setup_research_logging()
    old_file_handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler, logging.FileHandler)
    ]

    setup_research_logging()

    assert old_file_handlers
    assert all(handler.stream is None for handler in old_file_handlers)
