"""Bearer-token auth middleware for the hosted MCP server.

Rejects requests missing a valid `Authorization: Bearer $MCP_AUTH_TOKEN`.
Exempts `/health` so Railway's healthcheck passes without a token.
No-op when `MCP_AUTH_TOKEN` is unset (local dev).
"""
from __future__ import annotations

import hmac
import logging
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

_PUBLIC_PATHS: set[str] = {"/health"}


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Constant-time Bearer-token check for MCP traffic."""

    def __init__(self, app):
        super().__init__(app)
        self._token = os.getenv("MCP_AUTH_TOKEN") or None
        if self._token is None:
            if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_SERVICE_ID"):
                raise RuntimeError("MCP_AUTH_TOKEN must be set for Railway MCP deployments")
            logger.warning(
                "MCP_AUTH_TOKEN is unset; MCP server is running unauthenticated. "
                "Set it in Railway env before exposing a public URL."
            )

    async def dispatch(self, request: Request, call_next):
        if self._token is None:
            return await call_next(request)

        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        header = request.headers.get("authorization", "")
        if not header.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing Authorization: Bearer <token> header"},
            )

        provided = header.split(" ", 1)[1].strip()
        if not provided or not hmac.compare_digest(provided, self._token):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid bearer token"},
            )

        return await call_next(request)
