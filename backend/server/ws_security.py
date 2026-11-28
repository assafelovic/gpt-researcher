"""Optional hardening for the ``/ws`` endpoint.

Origin validation (on by default)
    Browsers attach an ``Origin`` header to every WebSocket handshake, and CORS
    does not apply to WebSockets. Without a check, any web page open in the
    operator's browser can open a socket to a locally running backend. The
    following are allowed:

    * handshakes without an ``Origin`` header (CLI scripts and other
      non-browser clients);
    * loopback origins (``localhost``, ``127.0.0.1``, ``[::1]``) on any port;
    * the origins already trusted for CORS (``CORS_ALLOW_ORIGINS``), unless
      ``ALLOWED_WS_ORIGINS`` is set, in which case that comma-separated list is
      used instead.

    ``ALLOWED_WS_ORIGINS=*`` disables the check.

Client-supplied MCP stdio servers (off by default)
    With ``RESTRICT_CLIENT_MCP_STDIO=true``, MCP server definitions received
    from WebSocket clients are kept only when they use a network transport
    (``http``, ``https``, ``ws``, ``wss``), so a client cannot choose a local
    command to run. The default keeps the existing behaviour.
"""

import logging
import os
from typing import Any, Iterable, Optional
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
NETWORK_MCP_SCHEMES = frozenset({"http", "https", "ws", "wss"})
_TRUTHY = {"1", "true", "yes", "on"}


def _normalize_origin(origin: str) -> Optional[str]:
    """Return ``scheme://host[:port]`` in lower case, or ``None`` if not a plain http(s) origin."""
    if not isinstance(origin, str) or "\\" in origin:
        return None
    try:
        parts = urlsplit(origin.strip())
        port = parts.port
    except ValueError:
        return None
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return None
    if parts.username or parts.password or parts.path not in ("", "/") or parts.query or parts.fragment:
        return None
    host = f"[{parts.hostname}]" if ":" in parts.hostname else parts.hostname
    default_port = 80 if parts.scheme == "http" else 443
    return f"{parts.scheme}://{host}" + (f":{port}" if port and port != default_port else "")


def is_ws_origin_allowed(origin: Optional[str], cors_origins: Iterable[str] = ()) -> bool:
    """Decide whether a WebSocket handshake with this ``Origin`` header may proceed."""
    if origin is None:
        return True  # non-browser client

    configured = os.getenv("ALLOWED_WS_ORIGINS", "").strip()
    entries = [e.strip() for e in configured.split(",")] if configured else [str(e).strip() for e in cors_origins]
    if "*" in entries:
        return True

    normalized = _normalize_origin(origin)
    if normalized is None:
        return False  # includes the opaque origin "null"
    if urlsplit(normalized).hostname in LOOPBACK_HOSTS:
        return True
    return normalized in {n for n in map(_normalize_origin, entries) if n}


def _uses_network_transport(config: Any) -> bool:
    """Mirror MCPClientManager.convert_configs_to_langchain_format() transport selection."""
    if not isinstance(config, dict):
        return False
    url = config.get("connection_url")
    if not isinstance(url, str) or not url:
        return False
    try:
        return urlsplit(url).scheme.lower() in NETWORK_MCP_SCHEMES
    except ValueError:
        return False


def restrict_client_mcp_configs(mcp_configs: Any) -> Any:
    """Drop stdio-bound MCP configs when ``RESTRICT_CLIENT_MCP_STDIO`` is enabled (off by default)."""
    if not mcp_configs or os.getenv("RESTRICT_CLIENT_MCP_STDIO", "").strip().lower() not in _TRUTHY:
        return mcp_configs
    configs = mcp_configs if isinstance(mcp_configs, list) else []
    kept = [config for config in configs if _uses_network_transport(config)]
    if len(kept) != len(configs) or not isinstance(mcp_configs, list):
        logger.warning(
            "RESTRICT_CLIENT_MCP_STDIO is enabled: ignored %d client-supplied MCP server "
            "definition(s) that would use the local stdio transport",
            len(configs) - len(kept) if isinstance(mcp_configs, list) else 1,
        )
    return kept
