#!/usr/bin/env bash
# ============================================================================
# GPT Researcher - E2E Test Runner
#
# Startet Backend + (optional) Next.js, führt Playwright-Tests aus,
# erzeugt Screenshots und hinterlässt bei Fehlern GitHub Issues.
#
# Usage:
#   bash tests/e2e/run-e2e.sh                         # Nur Backend + Tests
#   bash tests/e2e/run-e2e.sh --nextjs                 # Backend + Next.js + Tests
#   bash tests/e2e/run-e2e.sh --project=vanilla        # Nur Vanilla
#   bash tests/e2e/run-e2e.sh --project=nextjs         # Nur Next.js
#   bash tests/e2e/run-e2e.sh --project=api            # Nur API
#   bash tests/e2e/run-e2e.sh --ci                     # CI-Modus (Tests nur)
#   make e2e                                           # via Makefile
#   make e2e-nextjs                                    # via Makefile mit Next.js
#   make e2e-ci                                        # via Makefile CI-Modus
#
# Der Loop startet Backend (Port 8002) und optional Next.js (Port 3000),
# führt alle 9 E2E-Tests (4x Vanilla, 3x Next.js, 2x API) aus,
# speichert Screenshots nach jedem Testschritt und generiert HTML-Report.
#
# Artefakte:
#   tests/e2e/screenshots/        Screenshots pro Testschritt
#   tests/e2e/playwright-report/  HTML-Report der Testlaeufe
#
# Env-Vars:
#   GITHUB_TOKEN            Für Issue-Erstellung via GitHub API
#   GITHUB_REPO             GitHub-Repo (Default: assafelovic/gpt-researcher)
#   VANILLA_URL             Vanilla-Frontend URL (Default: http://localhost:8002)
#   NEXTJS_URL              Next.js-Frontend URL (Default: http://localhost:3000)
#   E2E_HEADLESS            "false" für sichtbaren Browser (Default: true)
#   SCREENSHOT_DIR          Verzeichnis für Screenshots (Default: tests/e2e/screenshots/)
#   BACKEND_PORT            Backend-Port (Default: 8002)
#   NEXTJS_PORT             Next.js-Port (Default: 3000)
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8002}"
NEXTJS_PORT="${NEXTJS_PORT:-3000}"
E2E_HEADLESS="${E2E_HEADLESS:-true}"
SCREENSHOT_DIR="${SCREENSHOT_DIR:-$SCRIPT_DIR/screenshots}"
export SCREENSHOT_DIR

# ── Args ────────────────────────────────────────────────────────────────────
RUN_NEXTJS=false
CI_MODE=false
PLAYWRIGHT_ARGS=()

for arg in "$@"; do
  case "$arg" in
    --nextjs)    RUN_NEXTJS=true ;;
    --ci)        CI_MODE=true ;;
    --project=*) PLAYWRIGHT_ARGS+=("$arg") ;;
    --help|-h)
      echo "Usage: $0 [--nextjs] [--ci] [--project=vanilla|nextjs|api]"
      exit 0 ;;
    *) PLAYWRIGHT_ARGS+=("$arg") ;;
  esac
done

# ── Farben ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[E2E]${NC} $*"; }
ok()    { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
fail()  { echo -e "${RED}[✗]${NC} $*"; exit 1; }

# ── Cleanup ─────────────────────────────────────────────────────────────────
cleanup() {
  info "Räume Hintergrundprozesse auf ..."
  [ -n "${BACKEND_PID:-}" ] && kill "$BACKEND_PID" 2>/dev/null && ok "Backend gestoppt"
  [ -n "${NEXTJS_PID:-}" ]  && kill "$NEXTJS_PID" 2>/dev/null  && ok "Next.js gestoppt"
  wait 2>/dev/null
}
trap cleanup EXIT INT TERM

# ── Healthcheck ─────────────────────────────────────────────────────────────
wait_for_port() {
  local url="$1" name="$2" timeout="${3:-60}"
  info "Warte auf $name ($url) ..."
  for i in $(seq 1 "$timeout"); do
    if curl -sf "$url" >/dev/null 2>&1; then
      ok "$name ist bereit (${i}s)"
      return 0
    fi
    sleep 1
  done
  fail "$name nach ${timeout}s nicht erreichbar"
}

# ── Run: Backend ────────────────────────────────────────────────────────────
start_backend() {
  info "Starte Backend (Port $BACKEND_PORT) ..."
  cd "$PROJECT_DIR/backend"
  python3 run_server.py &
  BACKEND_PID=$!
  cd "$PROJECT_DIR"
  wait_for_port "http://localhost:$BACKEND_PORT" "Backend"
}

# ── Run: Next.js ────────────────────────────────────────────────────────────
start_nextjs() {
  info "Starte Next.js (Port $NEXTJS_PORT) ..."
  cd "$PROJECT_DIR/frontend/nextjs"
  npm run dev &
  NEXTJS_PID=$!
  cd "$PROJECT_DIR"
  wait_for_port "http://localhost:$NEXTJS_PORT" "Next.js"
}

# ── Run: Tests ──────────────────────────────────────────────────────────────
run_tests() {
  info "Installiere Dependencies (falls nötig) ..."
  cd "$SCRIPT_DIR"
  npm install --silent 2>/dev/null

  if [ ! -f node_modules/.playwright-browser-installed ]; then
    info "Installiere Chromium für Playwright ..."
    npx playwright install chromium 2>&1 | tail -1
    touch node_modules/.playwright-browser-installed
  fi

  mkdir -p "$SCRIPT_DIR/screenshots"
  mkdir -p "$SCRIPT_DIR/playwright-report"

  info "Starte Playwright-Tests ..."
  echo -e "${YELLOW}══════════════════════════════════════════════════════════${NC}"

  local pw_args=("${PLAYWRIGHT_ARGS[@]}")
  if [ "$E2E_HEADLESS" = "false" ] || [ "$E2E_HEADLESS" = "0" ]; then
    pw_args+=("--headed")
  fi

  if [ ${#pw_args[@]} -gt 0 ]; then
    npx playwright test "${pw_args[@]}"
  else
    npx playwright test
  fi

  local exit_code=$?
  echo -e "${YELLOW}══════════════════════════════════════════════════════════${NC}"

  if [ $exit_code -eq 0 ]; then
    ok "Alle E2E-Tests bestanden!"
  else
    fail "E2E-Tests fehlgeschlagen (Exit-Code: $exit_code)"
  fi
  return $exit_code
}

# ── Main ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        GPT Researcher - E2E Test Runner                  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$CI_MODE" = true ]; then
  run_tests
else
  start_backend
  [ "$RUN_NEXTJS" = true ] && start_nextjs
  run_tests
fi
