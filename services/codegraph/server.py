"""Streamable-HTTP MCP facade over GitNexus CLI for HLT estate repos.

GPT Researcher connects via CODEGRAPH_MCP_URL / CODEGRAPH_MCP_TOKEN.
Tools shell out to `gitnexus query|context|impact|trace|list` so the
structural graph stays the source of truth without embedding GitNexus.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="[%(asctime)s][%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("hlt-codegraph")

GITNEXUS_HOME = os.getenv("GITNEXUS_HOME", "/data/gitnexus")
REPOS_DIR = os.getenv("REPOS_DIR", "/data/repos")
AUTH_TOKEN = os.getenv("CODEGRAPH_MCP_TOKEN") or os.getenv("GITNEXUS_AUTH_TOKEN")


def _allowed_hosts() -> list[str]:
    configured = os.getenv("MCP_ALLOWED_HOSTS")
    if configured:
        return [host.strip() for host in configured.split(",") if host.strip()]
    port = os.getenv("PORT", "8080")
    hosts = [
        f"127.0.0.1:{port}",
        f"localhost:{port}",
        "127.0.0.1",
        "localhost",
        "0.0.0.0",
    ]
    # Render terminates TLS at the edge and forwards with the public Host
    # header, so the external hostname must be allowed for MCP clients.
    external = os.getenv("RENDER_EXTERNAL_HOSTNAME")
    if external:
        hosts.append(external)
    return hosts


def _run_gitnexus(args: list[str], timeout: int = 120) -> str:
    env = os.environ.copy()
    env["GITNEXUS_HOME"] = GITNEXUS_HOME
    try:
        completed = subprocess.run(
            ["gitnexus", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
    except FileNotFoundError:
        return json.dumps({"error": "gitnexus CLI not installed"})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "gitnexus command timed out", "args": args})

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    if completed.returncode != 0:
        return json.dumps(
            {
                "error": "gitnexus command failed",
                "args": args,
                "stdout": stdout[:4000],
                "stderr": stderr[:4000],
                "code": completed.returncode,
            }
        )
    return stdout or stderr or "{}"


mcp = FastMCP(
    name="HLT Codegraph",
    instructions=(
        "Structural code intelligence for HLT estate repos (mmm2, katailyst2, "
        "ebb, scrapervault, nursing-mastery). Prefer list_repos then query/"
        "context/impact/trace. Answers should stay architecture-aware."
    ),
    streamable_http_path="/mcp",
    transport_security=TransportSecuritySettings(allowed_hosts=_allowed_hosts()),
)


@mcp.tool()
def list_repos() -> str:
    """List indexed estate repositories available for structural queries."""
    return _run_gitnexus(["list"])


@mcp.tool()
def query(q: str, repo: str | None = None) -> str:
    """Hybrid search across the code knowledge graph."""
    args = ["query", q]
    if repo:
        args.extend(["--repo", repo])
    return _run_gitnexus(args)


@mcp.tool()
def context(symbol: str, repo: str | None = None) -> str:
    """360-degree view of a symbol: callers, callees, cluster participation."""
    args = ["context", symbol]
    if repo:
        args.extend(["--repo", repo])
    return _run_gitnexus(args)


@mcp.tool()
def impact(symbol: str, repo: str | None = None) -> str:
    """Blast-radius analysis for a symbol or file."""
    args = ["impact", symbol]
    if repo:
        args.extend(["--repo", repo])
    return _run_gitnexus(args)


@mcp.tool()
def trace(from_symbol: str, to_symbol: str, repo: str | None = None) -> str:
    """Shortest path between two symbols in the call graph."""
    args = ["trace", from_symbol, to_symbol]
    if repo:
        args.extend(["--repo", repo])
    return _run_gitnexus(args)


@mcp.tool()
def repo_overview(repo: str) -> str:
    """Plain-English overview: path on disk plus gitnexus status for one repo."""
    path = os.path.join(REPOS_DIR, repo)
    status = _run_gitnexus(["status"], timeout=60)
    listing = _run_gitnexus(["list"], timeout=60)
    return json.dumps(
        {
            "repo": repo,
            "path": path,
            "exists": os.path.isdir(path),
            "status": status,
            "registry": listing,
        }
    )


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):  # noqa: ANN001
    repos = []
    if os.path.isdir(REPOS_DIR):
        repos = sorted(
            name
            for name in os.listdir(REPOS_DIR)
            if os.path.isdir(os.path.join(REPOS_DIR, name))
        )
    return JSONResponse(
        {
            "status": "ok",
            "service": "hlt-codegraph",
            "repos": repos,
            "gitnexus_home": GITNEXUS_HOME,
            "auth_required": bool(AUTH_TOKEN),
        }
    )


class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/health", "/"}:
            return await call_next(request)
        if not AUTH_TOKEN:
            return await call_next(request)
        auth = request.headers.get("authorization", "")
        provided = ""
        if auth.lower().startswith("bearer "):
            provided = auth[7:].strip()
        if provided != AUTH_TOKEN:
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)


app = mcp.streamable_http_app()
app.add_middleware(BearerAuthMiddleware)


def run() -> None:
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    run()
