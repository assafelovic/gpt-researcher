#!/usr/bin/env python3
"""Minimal Katailyst2 MCP client (streamable HTTP) for registry operations.

Usage:
  python scripts/katailyst_mcp.py list-tools
  python scripts/katailyst_mcp.py describe <tool>
  python scripts/katailyst_mcp.py call <tool> '<json-arguments>'

Auth comes from KATAILYST2_MCP_TOKEN / KATAILYST_MCP_TOKEN env (inject with
`railway run` or `doppler run` — never paste values).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

URL = os.getenv("KATAILYST2_MCP_URL", "https://katailyst2.vercel.app/mcp")
TOKEN = os.getenv("KATAILYST2_MCP_TOKEN") or os.getenv("KATAILYST_MCP_TOKEN")

_session_id: str | None = None


def _rpc(method: str, params: dict | None = None, request_id: int = 1) -> dict:
    global _session_id
    payload: dict = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        payload["params"] = params
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    toolset = os.getenv("KATAILYST_TOOLSET")
    if toolset:
        headers["X-Katailyst-Toolset"] = toolset
    if _session_id:
        headers["Mcp-Session-Id"] = _session_id
    request = urllib.request.Request(
        URL, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        session = response.headers.get("Mcp-Session-Id")
        if session:
            _session_id = session
        raw = response.read().decode("utf-8")
    # Streamable HTTP may answer as SSE; extract the data line(s).
    if raw.lstrip().startswith("event:") or "\ndata:" in raw or raw.startswith("data:"):
        for line in raw.splitlines():
            if line.startswith("data:"):
                raw = line[len("data:"):].strip()
                break
    return json.loads(raw)


def initialize() -> None:
    _rpc(
        "initialize",
        {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "hlt-gpt-researcher-registrar", "version": "1.0"},
        },
    )
    # notifications/initialized (no response expected; ignore errors)
    try:
        _rpc("notifications/initialized")
    except Exception:
        pass


def main() -> None:
    if not TOKEN:
        sys.exit("KATAILYST2_MCP_TOKEN env is required")
    command = sys.argv[1] if len(sys.argv) > 1 else "list-tools"
    initialize()

    if command == "list-tools":
        result = _rpc("tools/list", {}, request_id=2)
        tools = result.get("result", {}).get("tools", [])
        for tool in tools:
            print(f"- {tool['name']}: {(tool.get('description') or '')[:120]}")
    elif command == "describe":
        result = _rpc("tools/list", {}, request_id=2)
        tools = result.get("result", {}).get("tools", [])
        wanted = sys.argv[2]
        for tool in tools:
            if tool["name"] == wanted:
                print(json.dumps(tool, indent=2))
                return
        sys.exit(f"tool {wanted} not found")
    elif command == "call":
        name = sys.argv[2]
        arguments = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        result = _rpc("tools/call", {"name": name, "arguments": arguments}, request_id=3)
        print(json.dumps(result, indent=2)[:8000])
    else:
        sys.exit(f"unknown command {command}")


if __name__ == "__main__":
    main()
