#!/usr/bin/env bash
# deploy-to-railway.sh — one-shot Railway deploy for GPT Researcher.
#
# Precondition: you are logged in to Railway CLI.
#   railway whoami   # should print your email
# If not: `railway login` first (opens browser).
#
# What this script does (read before you run):
#
#   1. Fails fast if railway CLI is missing or not logged in.
#   2. Creates or selects a Railway project named "gpt-researcher".
#   3. Creates a service, links the local repo.
#   4. Pushes the required env vars (OPENAI_API_KEY, TAVILY_API_KEY) from your
#      local .env file OR prompts for them if absent. NEVER prints the values.
#   5. Triggers the first deploy using the Procfile + railway.toml in this
#      repo (so the entrypoint is `backend.server.app:app`, not the broken
#      `backend.server.server:app` that the upstream Procfile shipped with).
#   6. Prints the public URL once the deploy is live, and runs one smoke curl
#      against /api/quick_search to confirm end-to-end.
#
# The deploy takes ~5-8 min for the first build (Python 3.13 + pip install +
# a few GB of dependencies). Subsequent deploys are faster.
#
# Cost: $0 for the first $5/month of Railway credit if you're on the Hobby
# plan. Usage-based after that; expected burn is single-digit dollars/month
# for light HLT internal use.

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"

echo "=== 1. Railway CLI health check ==="
if ! command -v railway >/dev/null 2>&1; then
  echo "  ERROR: railway CLI not installed. See https://docs.railway.com/guides/cli"
  echo "         macOS: brew install railway"
  exit 1
fi
if ! railway whoami >/dev/null 2>&1; then
  echo "  ERROR: not logged in. Run: railway login"
  exit 1
fi
whoami_out="$(railway whoami)"
echo "  ✓ logged in as: ${whoami_out}"

echo ""
echo "=== 2. Verify Procfile entrypoint is correct ==="
expected_proc='web: python -m uvicorn backend.server.app:app --host=0.0.0.0 --port=${PORT}'
if ! grep -qF "backend.server.app:app" Procfile; then
  echo "  ERROR: Procfile entrypoint is NOT backend.server.app:app"
  echo "         (current content: $(cat Procfile))"
  echo "         The upstream Procfile ships a broken entrypoint —"
  echo "         this script refuses to deploy a broken Procfile."
  exit 1
fi
echo "  ✓ Procfile entrypoint matches backend.server.app:app"

echo ""
echo "=== 3. Verify OPENAI_API_KEY + TAVILY_API_KEY in local env ==="
if [ ! -f .env ]; then
  echo "  ERROR: .env not found in $here"
  echo "         Restore from ~/secrets-backup-2026-04-17/gpt-researcher.env or"
  echo "         paste your keys manually. Required: OPENAI_API_KEY, TAVILY_API_KEY."
  exit 1
fi
for k in OPENAI_API_KEY TAVILY_API_KEY; do
  if ! grep -qE "^${k}=" .env; then
    echo "  ERROR: ${k} is missing from .env"
    exit 1
  fi
  # Sanity check key is non-empty (don't print value)
  val_len=$(grep -E "^${k}=" .env | head -1 | sed "s/^${k}=//" | tr -d '"' | tr -d "'" | wc -c)
  if [ "$val_len" -lt 10 ]; then
    echo "  ERROR: ${k} looks empty or too short in .env (< 10 chars)"
    exit 1
  fi
done
echo "  ✓ OPENAI_API_KEY present"
echo "  ✓ TAVILY_API_KEY present"

echo ""
echo "=== 4. Project + service setup ==="
# Detect whether this repo is already linked
if railway status >/dev/null 2>&1; then
  echo "  ✓ already linked to a Railway project"
  railway status 2>&1 | head -6
else
  echo "  Creating new Railway project 'gpt-researcher'..."
  railway init --name gpt-researcher
fi

# Railway CLI v4.x decoupled project creation from service creation.
# `railway init` creates the project; a service must be added explicitly
# before `railway variables --set` or `railway up` will work.
# Detect "Service: None" and auto-create the service (idempotent).
if railway status 2>&1 | grep -qE "^Service:\s*None"; then
  echo "  No service linked yet — creating one (required by Railway CLI v4.x)..."
  # --service <name> creates an empty service and auto-links this dir to it.
  # `yes ""` answers the "Enter a variable" prompt with a blank to let it proceed.
  if ! yes "" 2>/dev/null | railway add --service gpt-researcher >/dev/null 2>&1; then
    echo "  ERROR: railway add --service gpt-researcher failed. Run it manually and re-invoke this script."
    exit 1
  fi
  # Verify linkage worked
  if railway status 2>&1 | grep -qE "^Service:\s*None"; then
    echo "  ERROR: service still not linked after 'railway add'. Check 'railway status' manually."
    exit 1
  fi
  echo "  ✓ service 'gpt-researcher' created + linked"
fi

echo ""
echo "=== 5. Push env vars (values never printed) ==="
# Read each line from .env, skip comments + blanks, pipe to railway variables
while IFS='=' read -r k v; do
  [[ -z "$k" || "$k" =~ ^# ]] && continue
  [[ -z "$v" ]] && continue
  # Strip wrapping quotes if any
  v="${v%\"}"; v="${v#\"}"
  v="${v%\'}"; v="${v#\'}"
  railway variables --set "${k}=${v}" >/dev/null
  echo "  ✓ set ${k}"
done < .env

echo ""
echo "=== 6. Deploy ==="
# --detach so we get the URL back without streaming build logs
railway up --detach

echo ""
echo "=== 7. Allocate + confirm public URL ==="
# Railway v4.x: `railway domain` with no args ALLOCATES a domain if none
# exists and prints it. If one already exists it just prints it. So this
# call works whether it's first-deploy or a re-deploy.
url=""
raw="$(railway domain 2>&1 || true)"
if echo "$raw" | grep -qE "https?://"; then
  url="$(echo "$raw" | grep -oE 'https?://[^ ]+' | head -1)"
  echo "  ✓ public URL: $url"
else
  # Unusual — some Railway states don't allocate on the first call. Retry
  # with a few-second delay before giving up.
  for i in $(seq 1 12); do
    sleep 5
    raw="$(railway domain 2>&1 || true)"
    if echo "$raw" | grep -qE "https?://"; then
      url="$(echo "$raw" | grep -oE 'https?://[^ ]+' | head -1)"
      echo "  ✓ public URL (after ${i}x5s wait): $url"
      break
    fi
  done
fi

if [ -z "$url" ]; then
  echo "  WARN: domain not allocated after retry — check 'railway domain' manually."
  echo "  If Railway says 'no domain yet', try: railway domain generate (on CLIs where it exists)"
  exit 0
fi

echo ""
echo "=== 8. Smoke test /api/quick_search ==="
echo "  NOTE: first request may take 20-30s while the container cold-starts"
resp_code="$(curl -sS -o /tmp/gptr-smoke.json -w '%{http_code}' -X POST \
  "${url}/api/quick_search" \
  -H 'Content-Type: application/json' \
  -d '{"query":"NCLEX-RN pass rate 2026","summary":true}' || echo "000")"
if [ "$resp_code" = "200" ]; then
  echo "  ✓ HTTP 200 from ${url}/api/quick_search"
  echo "  response preview:"
  head -c 500 /tmp/gptr-smoke.json
  echo ""
else
  echo "  ⚠ HTTP ${resp_code} — not 200. Check 'railway logs' for details."
fi

echo ""
echo "=== 9. Done ==="
echo "  Public URL: $url"
echo ""
echo "  Next step: register tool:gpt-researcher.quick-search in Katailyst"
echo "  (see docs/runbooks/gpt-researcher/register-in-katailyst.md)"
