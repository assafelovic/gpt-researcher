#!/usr/bin/env bash
set -euo pipefail

export HERMES_HOME="${HERMES_HOME:-/data/hermes}"
mkdir -p "$HERMES_HOME"

python /app/seed_memory.py

# Prefer real Hermes CLI when installed; otherwise run a thin health gateway
# that documents readiness until Hermes is fully configured on the VM.
if command -v hermes >/dev/null 2>&1; then
  echo "[hermes] starting hermes gateway"
  # Common patterns across Hermes releases — try gateway, then serve.
  if hermes gateway --help >/dev/null 2>&1; then
    exec hermes gateway
  elif hermes serve --help >/dev/null 2>&1; then
    exec hermes serve
  else
    echo "[hermes] CLI present but no gateway/serve; falling back to health app"
  fi
fi

echo "[hermes] running readiness gateway (install/configure Hermes CLI for full agent)"
exec python /app/health_gateway.py
