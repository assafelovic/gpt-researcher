"""Hosted streamable-HTTP MCP server for GPT Researcher."""
from __future__ import annotations

import logging
import os

import uvicorn
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse

from mcp_server.auth import BearerAuthMiddleware
from mcp_server.tools import register_tools

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="[%(asctime)s][%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _allowed_hosts() -> list[str]:
    configured = os.getenv("MCP_ALLOWED_HOSTS")
    if configured:
        return [host.strip() for host in configured.split(",") if host.strip()]
    return [
        "127.0.0.1",
        "localhost",
        "0.0.0.0",
        "gpt-researcher-mcp-production.up.railway.app",
    ]

mcp = FastMCP(
    name="GPT Researcher",
    instructions=(
        "Use GPT Researcher for current web research. Start with quick_search "
        "for fast lookups or deep_research when you need a richer source-backed context."
    ),
    streamable_http_path="/mcp",
    transport_security=TransportSecuritySettings(allowed_hosts=_allowed_hosts()),
)
register_tools(mcp)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):  # noqa: D401, ANN001
    return JSONResponse(
        {
            "status": "ok",
            "service": "gpt-researcher-mcp",
            "version": os.getenv("RAILWAY_GIT_COMMIT_SHA", "local")[:7],
            "deploy_marker": os.getenv("HLT_DEPLOY_MARKER", "local"),
        }
    )


app = mcp.streamable_http_app()
app.add_middleware(BearerAuthMiddleware)


def run_server() -> None:
    """Run the MCP app for local `python -m mcp_server.server` use."""

    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("mcp_server.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    run_server()
