"""HLT-specific extensions for the GPT Researcher FastAPI app.

This module is isolated from upstream code so it can be regenerated or
re-applied after upstream merges without touching `backend/server/app.py`
beyond a single import line.

Adds:
  1. `GET /health` - dedicated liveness probe (Railway healthcheck target).
  2. `X-API-Key` middleware - rejects unauthenticated requests outside the
     frontend shell and static assets. Set `API_AUTH_KEY` in Railway env; if
     unset, the middleware is a no-op (useful for local dev).

Usage (one line at the bottom of `app.py`):

    from server.hlt_extensions import install as install_hlt_extensions
    install_hlt_extensions(app)

Upstream merges: if `app.py` is regenerated, just re-add that one import.
"""
from __future__ import annotations

import hmac
import logging
import os
import secrets
import time
from typing import Any, Iterable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)
_WS_TOKEN_TTL_SECONDS = 120

# Paths that must remain callable without auth so the frontend + Railway
# healthcheck + static assets keep working. Tight allowlist — every other
# route requires `X-API-Key`.
_PUBLIC_EXACT: set[str] = {"/", "/health", "/favicon.ico"}
_PUBLIC_PREFIXES: tuple[str, ...] = (
    "/site/",      # Next.js static build
    "/static/",    # Any static mounts
)

_SCOPE_INSTRUCTIONS = {
    "codebase": (
        "Use available codebase/repository context. Prefer implementation files, "
        "repo maps, pull requests, and architecture notes over generic web sources."
    ),
    "cms": (
        "Use available Katailyst CMS, registry, knowledge-base, playbook, and "
        "ecosystem-map context when it is relevant to the question."
    ),
    "metrics": (
        "Use available metrics/analytics context, including Metabase-backed data, "
        "when it is relevant. Clearly separate measured data from inference."
    ),
    "firecrawl": (
        "For external pages, prefer high-quality extraction and crawling when the "
        "deployment has Firecrawl configured."
    ),
}

_DEPTH_INSTRUCTIONS = {
    "fast": "Keep the research narrow and fast. Prioritize the most relevant sources.",
    "balanced": "Balance speed and depth. Use enough context to answer confidently.",
    "deep": "Go deeper. Compare sources, inspect primary context, and surface tradeoffs.",
}


def api_key_is_valid(provided: str | None) -> bool:
    """Return whether `provided` matches API_AUTH_KEY.

    When API_AUTH_KEY is unset, auth is intentionally disabled for local dev.
    """

    expected = os.getenv("API_AUTH_KEY") or None
    if expected is None:
        return True
    return bool(provided and hmac.compare_digest(provided, expected))


def create_websocket_token() -> str:
    """Create a short-lived token for browser WebSocket clients."""

    api_key = os.getenv("API_AUTH_KEY") or None
    if api_key is None:
        return "local-dev"

    issued_at = str(int(time.time()))
    nonce = secrets.token_urlsafe(18)
    payload = f"{issued_at}.{nonce}"
    signature = hmac.new(api_key.encode(), payload.encode(), "sha256").hexdigest()
    return f"{payload}.{signature}"


def websocket_token_is_valid(token: str | None) -> bool:
    """Validate a short-lived browser WebSocket token."""

    api_key = os.getenv("API_AUTH_KEY") or None
    if api_key is None:
        return True
    if not token:
        return False

    try:
        issued_at_text, nonce, provided_signature = token.split(".", 2)
        issued_at = int(issued_at_text)
    except (TypeError, ValueError):
        return False

    now = int(time.time())
    if issued_at > now + 30 or now - issued_at > _WS_TOKEN_TTL_SECONDS:
        return False

    payload = f"{issued_at_text}.{nonce}"
    expected_signature = hmac.new(api_key.encode(), payload.encode(), "sha256").hexdigest()
    return hmac.compare_digest(provided_signature, expected_signature)


def _bearer_headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _append_unique_mcp_config(configs: list[dict[str, Any]], config: dict[str, Any]) -> None:
    name = config.get("name")
    if name and any(existing.get("name") == name for existing in configs):
        return
    configs.append(config)


def expand_mcp_presets(mcp_configs: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Expand HLT server-side MCP presets without exposing tokens to browsers."""

    expanded: list[dict[str, Any]] = []
    for config in mcp_configs or []:
        preset = config.get("preset")
        if not preset:
            expanded.append(config)
            continue

        name = config.get("name") or preset
        if preset == "katailyst":
            url = os.getenv("KATAILYST_MCP_URL", "https://www.katailyst.com/mcp")
            token = os.getenv("KATAILYST_MCP_TOKEN") or os.getenv("KATAILYST_AUTH_TOKEN")
            if not token:
                logger.warning("Skipping Katailyst MCP preset: KATAILYST_MCP_TOKEN is unset")
                continue
            expanded.append({
                "name": name,
                "connection_url": url,
                "connection_type": "streamable_http",
                "connection_headers": _bearer_headers(token),
            })
        elif preset == "github":
            url = os.getenv("GITHUB_MCP_URL")
            token = os.getenv("GITHUB_MCP_TOKEN")
            if url:
                expanded.append({
                    "name": name,
                    "connection_url": url,
                    "connection_type": "streamable_http",
                    "connection_headers": _bearer_headers(token),
                })
            else:
                logger.warning("Skipping GitHub MCP preset: GITHUB_MCP_URL is unset")
        elif preset == "metabase":
            url = os.getenv("METABASE_MCP_URL")
            token = os.getenv("METABASE_MCP_TOKEN")
            if url:
                expanded.append({
                    "name": name,
                    "connection_url": url,
                    "connection_type": "streamable_http",
                    "connection_headers": _bearer_headers(token),
                })
            else:
                logger.warning("Skipping Metabase MCP preset: METABASE_MCP_URL is unset")
        else:
            logger.warning("Skipping unknown MCP preset: %s", preset)
    return expanded


def prepare_research_request(
    *,
    task: str,
    mcp_enabled: bool,
    mcp_strategy: str,
    mcp_configs: list[dict[str, Any]] | None,
    research_scope: dict[str, Any] | None,
) -> tuple[str, bool, str, list[dict[str, Any]], dict[str, Any]]:
    """Apply HLT research-scope metadata to a GPT Researcher request.

    This keeps the browser payload token-free. The frontend sends booleans such
    as `codebase` or `cms`; this server-side helper expands them into safe MCP
    presets and adds concise research instructions to the task.
    """

    scope = research_scope or {}
    enabled_keys = [
        key for key in ("codebase", "cms", "metrics", "firecrawl")
        if bool(scope.get(key))
    ]
    depth = scope.get("depth") if scope.get("depth") in _DEPTH_INSTRUCTIONS else "balanced"

    configs = list(mcp_configs or [])
    if scope.get("codebase") or scope.get("cms"):
        _append_unique_mcp_config(configs, {"name": "katailyst", "preset": "katailyst"})
    if scope.get("codebase"):
        _append_unique_mcp_config(configs, {"name": "github", "preset": "github"})
    if scope.get("metrics"):
        _append_unique_mcp_config(configs, {"name": "metabase", "preset": "metabase"})

    expanded_configs = expand_mcp_presets(configs)
    next_mcp_enabled = bool(mcp_enabled or expanded_configs)
    next_mcp_strategy = "fast" if depth == "fast" else "deep"

    if not enabled_keys and depth == "balanced":
        return task, next_mcp_enabled, mcp_strategy, expanded_configs, {
            "enabled_sources": [],
            "depth": depth,
            "mcp_server_count": len(expanded_configs),
        }

    instruction_lines = [_DEPTH_INSTRUCTIONS[depth]]
    instruction_lines.extend(_SCOPE_INSTRUCTIONS[key] for key in enabled_keys)
    scoped_task = (
        f"{task}\n\n"
        "HLT research scope instructions:\n"
        + "\n".join(f"- {line}" for line in instruction_lines)
    )

    return scoped_task, next_mcp_enabled, next_mcp_strategy, expanded_configs, {
        "enabled_sources": enabled_keys,
        "depth": depth,
        "mcp_server_count": len(expanded_configs),
    }


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Reject requests missing a valid `X-API-Key` header.

    No-op when `API_AUTH_KEY` env is unset (local dev / upstream default).
    """

    def __init__(self, app, api_key: str | None, public_exact: set[str], public_prefixes: tuple[str, ...]):
        super().__init__(app)
        self._api_key = api_key
        self._public_exact = public_exact
        self._public_prefixes = public_prefixes

    async def dispatch(self, request: Request, call_next):
        if self._api_key is None:
            return await call_next(request)

        path = request.url.path
        if path in self._public_exact or path.startswith(self._public_prefixes):
            return await call_next(request)

        # CORS preflight must pass; CORSMiddleware handles the actual check.
        if request.method == "OPTIONS":
            return await call_next(request)

        provided = request.headers.get("x-api-key", "")
        if not provided or not hmac.compare_digest(provided, self._api_key):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid X-API-Key header"},
            )
        return await call_next(request)


def install(
    app: FastAPI,
    *,
    extra_public_exact: Iterable[str] | None = None,
    extra_public_prefixes: Iterable[str] | None = None,
) -> None:
    """Attach HLT extensions to the given FastAPI app."""

    public_exact = set(_PUBLIC_EXACT)
    if extra_public_exact:
        public_exact.update(extra_public_exact)

    public_prefixes = list(_PUBLIC_PREFIXES)
    if extra_public_prefixes:
        public_prefixes.extend(extra_public_prefixes)

    # 1. /health — used by Railway healthcheckPath (see railway.toml).
    @app.get("/health", tags=["hlt"])
    def health():  # noqa: D401
        return {
            "status": "ok",
            "service": "gpt-researcher-api",
            "version": os.getenv("RAILWAY_GIT_COMMIT_SHA", "local")[:7],
            "deploy_marker": os.getenv("HLT_DEPLOY_MARKER", "local"),
        }

    # 2. API-key auth (opt-in via env).
    api_key = os.getenv("API_AUTH_KEY") or None
    app.add_middleware(
        APIKeyMiddleware,
        api_key=api_key,
        public_exact=public_exact,
        public_prefixes=tuple(public_prefixes),
    )

    if api_key:
        logger.info("HLT extensions: /health + X-API-Key middleware installed (auth enabled)")
    else:
        logger.info("HLT extensions: /health installed; auth disabled (API_AUTH_KEY unset)")
