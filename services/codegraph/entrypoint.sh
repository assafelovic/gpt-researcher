#!/usr/bin/env bash
set -euo pipefail

export GITNEXUS_HOME="${GITNEXUS_HOME:-/data/gitnexus}"
export REPOS_DIR="${REPOS_DIR:-/data/repos}"
mkdir -p "$GITNEXUS_HOME" "$REPOS_DIR"

# Run the boot reindex in the background so the MCP server binds its port
# immediately — Render fails the deploy if nothing listens within the scan
# window, and a full 5-repo index takes longer than that.
if [[ "${CODEGRAPH_SKIP_INDEX_ON_BOOT:-0}" != "1" ]]; then
  (
    echo "[codegraph] boot reindex (background)"
    /app/reindex.sh || echo "[codegraph] boot reindex failed (continuing with existing indexes)"
  ) &
fi

# Optional background reindex loop (hours). 0 disables.
INTERVAL_HOURS="${CODEGRAPH_REINDEX_HOURS:-24}"
if [[ "$INTERVAL_HOURS" != "0" ]]; then
  (
    while true; do
      sleep "$((INTERVAL_HOURS * 3600))"
      echo "[codegraph] scheduled reindex"
      /app/reindex.sh || true
    done
  ) &
fi

exec python /app/server.py
