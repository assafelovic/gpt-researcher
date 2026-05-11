"""Network helpers for research modes that require special routing."""

from __future__ import annotations

import os
from typing import Any


ONION_PROXY_ENV_VARS = (
    "ONION_PROXY_URL",
    "TOR_HTTP_PROXY",
    "TOR_PROXY_URL",
)


def resolve_onion_proxy_url(cfg: Any | None = None) -> str | None:
    """Return a configured proxy URL for onion/Tor research, if any.

    The helper intentionally only checks onion-specific variables so regular
    corporate or system proxies are not silently repurposed for Tor traffic.
    """
    if cfg is not None:
        candidate = getattr(cfg, "onion_proxy_url", None)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()

    for env_name in ONION_PROXY_ENV_VARS:
        candidate = os.getenv(env_name)
        if candidate and candidate.strip():
            return candidate.strip()

    return None


def build_requests_proxies(proxy_url: str | None) -> dict[str, str] | None:
    """Build a requests-compatible proxy mapping."""
    if not proxy_url:
        return None
    return {"http": proxy_url, "https": proxy_url}

