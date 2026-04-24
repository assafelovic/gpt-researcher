from starlette.testclient import TestClient

from mcp_server.server import app


def test_mcp_health_includes_redacted_langfuse_status():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    langfuse = body["observability"]["langfuse"]
    assert body["service"] == "gpt-researcher-mcp"
    assert set(langfuse) >= {
        "configured",
        "package_available",
        "public_key",
        "secret_key",
        "base_url",
        "record_io",
    }
    assert "sk-" not in str(body)
    assert "pk-" not in str(body)
