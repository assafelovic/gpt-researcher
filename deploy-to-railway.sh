#!/usr/bin/env bash
# Deploy the GPT Researcher FastAPI/frontend service to Railway.

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"

project_name="${RAILWAY_PROJECT_NAME:-gpt-researcher}"
service_name="${RAILWAY_API_SERVICE:-gpt-researcher-api}"
deploy_marker="api-$(date +%Y%m%d%H%M%S)-$RANDOM"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: missing required command: $1"
    exit 1
  fi
}

env_value() {
  local key="$1"
  awk -F= -v key="$key" '
    $0 !~ /^[[:space:]]*#/ && $1 == key {
      sub("^[^=]*=", "")
      gsub(/^["'\'']|["'\'']$/, "")
      print
      exit
    }
  ' .env
}

require_env() {
  local key="$1"
  local value
  value="$(env_value "$key")"
  if [ "${#value}" -lt 10 ]; then
    echo "ERROR: $key is missing or too short in .env"
    exit 1
  fi
}

ensure_project() {
  if railway status >/dev/null 2>&1; then
    echo "  linked to Railway project"
  else
    echo "  creating Railway project: $project_name"
    railway init --name "$project_name"
  fi
}

ensure_service() {
  local service="$1"
  if railway service status --service "$service" >/dev/null 2>&1; then
    echo "  service exists: $service"
    return
  fi

  echo "  creating service: $service"
  if ! yes "" 2>/dev/null | railway add --service "$service" >/dev/null; then
    if railway service status --service "$service" >/dev/null 2>&1; then
      echo "  service exists after add: $service"
      return
    fi
    echo "ERROR: failed to create Railway service '$service'"
    exit 1
  fi
}

push_env_file() {
  local service="$1"
  while IFS='=' read -r key value; do
    [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${value:-}" ]] && continue
    value="${value%\"}"; value="${value#\"}"
    value="${value%\'}"; value="${value#\'}"
    railway variable set --service "$service" --skip-deploys "${key}=${value}" >/dev/null
    echo "  set $key"
  done < .env
}

domain_for_service() {
  local service="$1"
  local raw url
  raw="$(railway domain --service "$service" 2>&1 || true)"
  url="$(echo "$raw" | grep -oE 'https?://[^ ]+' | head -1 || true)"
  if [ -n "$url" ]; then
    echo "$url"
    return
  fi

  for _ in $(seq 1 12); do
    sleep 5
    raw="$(railway domain --service "$service" 2>&1 || true)"
    url="$(echo "$raw" | grep -oE 'https?://[^ ]+' | head -1 || true)"
    if [ -n "$url" ]; then
      echo "$url"
      return
    fi
  done
}

wait_for_health() {
  local url="$1"
  local expected_service="$2"
  local expected_marker="${3:-}"
  local body

  for i in $(seq 1 60); do
    body="$(curl -sS "$url/health" || true)"
    if echo "$body" | grep -q "\"service\":\"$expected_service\"" && {
      [ -z "$expected_marker" ] || echo "$body" | grep -q "\"deploy_marker\":\"$expected_marker\""
    }; then
      echo "$body" >/tmp/gptr-api-health.json
      return
    fi
    echo "  waiting for $expected_service /health (${i}/60)"
    sleep 10
  done

  echo "ERROR: $expected_service /health did not become ready"
  echo "$body"
  exit 1
}

echo "=== 1. Railway CLI health check ==="
require_cmd railway
require_cmd curl
if ! railway whoami >/dev/null 2>&1; then
  echo "ERROR: not logged in. Run: railway login"
  exit 1
fi
echo "  logged in as: $(railway whoami)"

echo ""
echo "=== 2. Verify API entrypoint and env ==="
if ! grep -qF "railway-start.sh" Procfile || [ ! -x railway-start.sh ]; then
  echo "ERROR: Procfile must use executable railway-start.sh"
  exit 1
fi
if [ ! -f .env ]; then
  echo "ERROR: .env not found in $here"
  exit 1
fi
require_env OPENAI_API_KEY
require_env TAVILY_API_KEY
require_env API_AUTH_KEY
api_auth_key="$(env_value API_AUTH_KEY)"
echo "  required env vars present"

echo ""
echo "=== 3. Project and service setup ==="
ensure_project
ensure_service "$service_name"

echo ""
echo "=== 4. Push env vars to $service_name ==="
push_env_file "$service_name"
railway variable set --service "$service_name" --skip-deploys "GPT_RESEARCHER_SERVICE=api" >/dev/null
echo "  set GPT_RESEARCHER_SERVICE"
railway variable set --service "$service_name" --skip-deploys "RAILPACK_START_CMD=./railway-start.sh" >/dev/null
echo "  set RAILPACK_START_CMD"
railway variable set --service "$service_name" --skip-deploys "RAILWAY_RUN_UID=0" >/dev/null
echo "  set RAILWAY_RUN_UID"
railway variable set --service "$service_name" --skip-deploys "HLT_DEPLOY_MARKER=$deploy_marker" >/dev/null
echo "  set HLT_DEPLOY_MARKER"

echo ""
echo "=== 5. Deploy $service_name ==="
railway up --service "$service_name" --detach

echo ""
echo "=== 6. Allocate and confirm public URL ==="
url="$(domain_for_service "$service_name")"
if [ -z "${url:-}" ]; then
  echo "ERROR: no public domain found for $service_name"
  exit 1
fi
echo "  public URL: $url"

echo ""
echo "=== 7. Smoke tests ==="
echo "  /health"
wait_for_health "$url" "gpt-researcher-api" "$deploy_marker"
cat /tmp/gptr-api-health.json
echo ""

echo "  unauthenticated /api/quick_search should be 401"
unauth_code="$(curl -sS -o /tmp/gptr-api-unauth.json -w '%{http_code}' -X POST \
  "$url/api/quick_search" \
  -H 'Content-Type: application/json' \
  -d '{"query":"NCLEX-RN pass rate 2026","summary":true}' || echo "000")"
if [ "$unauth_code" != "401" ]; then
  echo "ERROR: expected 401, got $unauth_code"
  cat /tmp/gptr-api-unauth.json || true
  exit 1
fi
echo "  got 401"

echo "  authenticated /api/quick_search should be 200"
auth_code="$(curl -sS -o /tmp/gptr-api-auth.json -w '%{http_code}' -X POST \
  "$url/api/quick_search" \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $api_auth_key" \
  -d '{"query":"NCLEX-RN pass rate 2026","summary":true}' || echo "000")"
if [ "$auth_code" != "200" ]; then
  echo "ERROR: expected 200, got $auth_code"
  cat /tmp/gptr-api-auth.json || true
  exit 1
fi
head -c 500 /tmp/gptr-api-auth.json
echo ""

echo ""
echo "Done. API URL: $url"
