#!/usr/bin/env bash
set -euo pipefail

export HERMES_HOME="${HERMES_HOME:-/data/hermes}"
mkdir -p "$HERMES_HOME"

python /app/seed_memory.py

# Full Hermes gateway only when explicitly enabled (needs Slack/OpenRouter keys).
# Default: readiness health gateway so the Render service stays green.
if [[ "${HERMES_ENABLE_GATEWAY:-0}" == "1" ]] && command -v hermes >/dev/null 2>&1; then
  echo "[hermes] starting hermes gateway (HERMES_ENABLE_GATEWAY=1)"
  export HERMES_ALLOW_ROOT_GATEWAY="${HERMES_ALLOW_ROOT_GATEWAY:-0}"
  if hermes gateway --help >/dev/null 2>&1; then
    exec hermes gateway
  elif hermes serve --help >/dev/null 2>&1; then
    exec hermes serve
  fi
  echo "[hermes] gateway subcommand missing; falling back to readiness app"
fi

echo "[hermes] running readiness gateway"
exec python /app/health_gateway.py
