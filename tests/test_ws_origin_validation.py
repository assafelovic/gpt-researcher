"""Origin validation for the /ws handshake (backend/server/ws_security.py)."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.server import app as app_module
from backend.server.ws_security import is_ws_origin_allowed

# The CORS_ALLOW_ORIGINS defaults from backend/server/app.py.
CORS_DEFAULTS = ["http://localhost:3000", "http://127.0.0.1:3000", "https://app.gptr.dev"]


@pytest.fixture(autouse=True)
def _no_ws_origin_override(monkeypatch):
    monkeypatch.delenv("ALLOWED_WS_ORIGINS", raising=False)


@pytest.mark.parametrize(
    "origin",
    [
        None,  # non-browser client (CLI script)
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://[::1]:8000",
        "HTTPS://LOCALHOST",
        "https://app.gptr.dev",
        "https://app.gptr.dev:443",
    ],
)
def test_default_policy_allows_non_browser_loopback_and_cors_origins(origin):
    assert is_ws_origin_allowed(origin, CORS_DEFAULTS)


@pytest.mark.parametrize(
    "origin",
    [
        "https://fixture.invalid",
        "http://localhost.fixture.invalid",
        "http://127.0.0.1.fixture.invalid",
        "http://localhost\\@fixture.invalid",
        "http://user@localhost",
        "ftp://localhost",
        "null",
        "",
    ],
)
def test_default_policy_rejects_cross_site_origins(origin):
    assert not is_ws_origin_allowed(origin, CORS_DEFAULTS)


def test_allowed_ws_origins_replaces_the_cors_list(monkeypatch):
    monkeypatch.setenv("ALLOWED_WS_ORIGINS", "https://app.fixture.invalid, http://10.0.0.5:8000")

    assert is_ws_origin_allowed("https://app.fixture.invalid", CORS_DEFAULTS)
    assert is_ws_origin_allowed("http://10.0.0.5:8000", CORS_DEFAULTS)
    assert is_ws_origin_allowed("http://localhost:3000", CORS_DEFAULTS)  # loopback stays allowed
    assert not is_ws_origin_allowed("https://app.gptr.dev", CORS_DEFAULTS)
    assert not is_ws_origin_allowed("https://other.fixture.invalid", CORS_DEFAULTS)


def test_wildcard_disables_the_check(monkeypatch):
    monkeypatch.setenv("ALLOWED_WS_ORIGINS", "*")
    assert is_ws_origin_allowed("https://fixture.invalid", CORS_DEFAULTS)


def test_ws_endpoint_rejects_a_cross_site_origin(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # the app lifespan creates ./outputs
    with TestClient(app_module.app) as client:
        with pytest.raises(WebSocketDisconnect) as excinfo:
            with client.websocket_connect("/ws", headers={"Origin": "https://fixture.invalid"}):
                pass
    assert excinfo.value.code == 1008


@pytest.mark.parametrize("headers", [{}, {"Origin": "http://localhost:3000"}], ids=["no-origin", "localhost"])
def test_ws_endpoint_accepts_local_and_non_browser_clients(monkeypatch, tmp_path, headers):
    monkeypatch.chdir(tmp_path)
    with TestClient(app_module.app) as client:
        with client.websocket_connect("/ws", headers=headers) as ws:
            ws.send_text("ping")
            assert ws.receive_text() == "pong"
