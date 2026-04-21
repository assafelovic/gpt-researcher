from typing import Dict, List, Optional


def _to_websocket_origin(origin: str) -> str:
    if origin.startswith("https://"):
        return "wss://" + origin[len("https://"):]
    if origin.startswith("http://"):
        return "ws://" + origin[len("http://"):]
    return origin


def build_agent_discovery_document(
    origin: str,
    domain: str,
    contact: Optional[str] = None,
) -> Dict[str, object]:
    normalized_origin = origin.rstrip("/")
    websocket_origin = _to_websocket_origin(normalized_origin)

    services: List[Dict[str, object]] = [
        {
            "name": "research",
            "description": "Submit a research job and generate a report.",
            "endpoint": f"{normalized_origin}/report/",
            "protocol": "http",
            "auth": "none",
            "governance": "none",
            "free_tier": True,
        },
        {
            "name": "reports",
            "description": "Create, list, and manage generated research reports.",
            "endpoint": f"{normalized_origin}/api/reports",
            "protocol": "http",
            "auth": "none",
            "governance": "none",
            "free_tier": True,
        },
        {
            "name": "chat",
            "description": "Ask follow-up questions against a generated report.",
            "endpoint": f"{normalized_origin}/api/chat",
            "protocol": "http",
            "auth": "none",
            "governance": "none",
            "free_tier": True,
        },
        {
            "name": "research_stream",
            "description": "Realtime WebSocket stream for interactive research runs.",
            "endpoint": f"{websocket_origin}/ws",
            "protocol": "websocket",
            "auth": "none",
            "governance": "none",
            "free_tier": True,
        },
    ]

    document: Dict[str, object] = {
        "agent_discovery_version": "0.1",
        "domain": domain,
        "services": services,
    }

    if contact:
        document["contact"] = contact

    return document
