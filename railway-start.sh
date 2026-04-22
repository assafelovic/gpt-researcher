#!/usr/bin/env bash
# Railway start dispatcher for the two HLT services that share this repo root.

set -euo pipefail

port="${PORT:-8000}"
service="${GPT_RESEARCHER_SERVICE:-${RAILWAY_SERVICE_NAME:-api}}"

echo "Starting GPT Researcher service target: ${service}"

case "$service" in
  gpt-researcher-mcp|mcp)
    exec python -m uvicorn mcp_server.server:app --host=0.0.0.0 --port="${port}"
    ;;
  *)
    exec python -m uvicorn backend.server.app:app --host=0.0.0.0 --port="${port}"
    ;;
esac
