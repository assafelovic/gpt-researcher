"""Lightweight readiness server when Hermes CLI is not yet fully wired."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="HLT Hermes readiness")
HERMES_HOME = Path(os.getenv("HERMES_HOME", "/data/hermes"))


@app.get("/health")
def health():
    memory = HERMES_HOME / "memory"
    seeds = sorted(p.name for p in memory.glob("*.md")) if memory.exists() else []
    return {
        "status": "ok",
        "service": "hlt-hermes",
        "mode": "readiness_gateway",
        "hermes_home": str(HERMES_HOME),
        "seeded_memory": seeds,
        "mcp_targets": {
            "gpt_researcher": bool(os.getenv("GPTR_MCP_URL")),
            "codegraph": bool(os.getenv("CODEGRAPH_MCP_URL")),
            "katailyst2": bool(os.getenv("KATAILYST2_MCP_URL")),
            "linear": bool(os.getenv("LINEAR_MCP_URL")),
        },
        "note": (
            "Set OPENROUTER_API_KEY + Slack tokens and ensure hermes CLI is "
            "installed so entrypoint starts the real gateway."
        ),
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
