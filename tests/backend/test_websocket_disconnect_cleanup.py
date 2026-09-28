"""A client closing /ws is a normal disconnect: clean up, don't log an error (#1586)."""

import logging
import time

from fastapi.testclient import TestClient

from backend.server import app as app_module


def _wait_for(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


def test_closed_socket_is_released_by_the_manager(caplog):
    manager = app_module.manager
    before = len(manager.active_connections)

    with caplog.at_level(logging.INFO):
        with TestClient(app_module.app) as client:
            with client.websocket_connect("/ws") as ws:
                ws.send_text("ping")
                assert ws.receive_text() == "pong"
                assert len(manager.active_connections) == before + 1
            # Leaving the block closes the socket from the client side.
            assert _wait_for(lambda: len(manager.active_connections) == before)

    assert not manager.sender_tasks and not manager.message_queues
    assert "WebSocket error" not in caplog.text
    assert "WebSocket disconnected" in caplog.text
