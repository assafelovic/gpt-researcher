#!/usr/bin/env python3
"""Smoke-test the deployed Vercel UI token route and Railway WebSocket path.

This intentionally exits after the first non-error stream event. The backend
will cancel the research task when the WebSocket closes, keeping the smoke test
cheap while still proving the browser-facing auth path and research start path.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import urllib.request

import websockets


def fetch_ws_token(ui_url: str) -> str:
    request = urllib.request.Request(f"{ui_url.rstrip('/')}/api/ws-token", method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
        payload = json.load(response)
    token = payload.get("ws_token")
    if not token:
        raise RuntimeError(f"No ws_token in response: {payload}")
    return token


async def smoke(args: argparse.Namespace) -> None:
    token = fetch_ws_token(args.ui_url)
    ws_url = args.api_url.rstrip("/").replace("https://", "wss://").replace("http://", "ws://")
    payload = {
        "task": args.query,
        "report_type": "research_report",
        "report_source": "web",
        "tone": "Objective",
        "query_domains": [],
        "mcp_enabled": False,
        "mcp_strategy": "fast",
        "mcp_configs": [],
    }

    async with websockets.connect(f"{ws_url}/ws?ws_token={token}") as websocket:
        await websocket.send("start " + json.dumps(payload))
        for attempt in range(args.max_messages):
            raw = await asyncio.wait_for(websocket.recv(), timeout=args.timeout)
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")

            if "name 'os' is not defined" in raw or "JSONDecodeError" in raw:
                raise RuntimeError(f"fatal startup error: {raw[:500]}")

            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                print(f"stream_text={raw[:160]}")
                return

            event_type = event.get("type")
            content = event.get("content")
            output = str(event.get("output", ""))
            print(f"stream_event_{attempt + 1}=type:{event_type} content:{content}")

            if event_type == "logs" and content == "error":
                raise RuntimeError(f"backend returned error event: {output[:500]}")
            if event_type:
                return

    raise RuntimeError("WebSocket closed before any stream event was observed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ui-url", default="https://gpt-researcher-ui.vercel.app")
    parser.add_argument("--api-url", default="https://gpt-researcher-api-production.up.railway.app")
    parser.add_argument("--query", default="smoke test: GPT Researcher WebSocket startup")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--max-messages", type=int, default=8)
    args = parser.parse_args()
    asyncio.run(smoke(args))


if __name__ == "__main__":
    main()
