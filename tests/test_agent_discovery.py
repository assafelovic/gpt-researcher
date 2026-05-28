import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "backend"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from backend.server.agent_discovery import build_agent_discovery_document


def test_build_agent_discovery_document_exposes_expected_services():
    document = build_agent_discovery_document(
        origin="https://gptr.dev",
        domain="gptr.dev",
        contact="team@gptr.dev",
    )

    assert document["agent_discovery_version"] == "0.1"
    assert document["domain"] == "gptr.dev"
    assert document["contact"] == "team@gptr.dev"

    services = {service["name"]: service for service in document["services"]}

    assert services["research"]["endpoint"] == "https://gptr.dev/report/"
    assert services["reports"]["endpoint"] == "https://gptr.dev/api/reports"
    assert services["chat"]["endpoint"] == "https://gptr.dev/api/chat"
    assert services["research_stream"]["endpoint"] == "wss://gptr.dev/ws"
    assert services["research_stream"]["protocol"] == "websocket"


def test_build_agent_discovery_document_omits_empty_contact():
    document = build_agent_discovery_document(
        origin="http://localhost:8000/",
        domain="localhost",
    )

    assert "contact" not in document

    services = {service["name"]: service for service in document["services"]}
    assert services["research"]["endpoint"] == "http://localhost:8000/report/"
    assert services["research_stream"]["endpoint"] == "ws://localhost:8000/ws"


def test_app_exposes_agent_discovery_route():
    source = (ROOT / "backend" / "server" / "app.py").read_text()

    assert '@app.get("/.well-known/agent-discovery.json")' in source
    assert 'build_agent_discovery_document(origin=origin, domain=domain, contact=contact)' in source
