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
from typing import Iterable

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
