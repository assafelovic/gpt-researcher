#!/usr/bin/env bash
set -euo pipefail

REPOS_DIR="${REPOS_DIR:-/data/repos}"
GITNEXUS_HOME="${GITNEXUS_HOME:-/data/gitnexus}"
export GITNEXUS_HOME

# slug|github_org/repo
DEFAULT_REPOS=(
  "mmm2|Awhitter/MMM2"
  "katailyst2|Awhitter/katailyst2"
  "ebb|Awhitter/evidence-based-business"
  "scrapervault|Awhitter/ScraperVault"
  "nursing-mastery|Awhitter/nursing-mastery"
)

TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
REPOS_SPEC="${CODEGRAPH_REPOS:-}"

mkdir -p "$REPOS_DIR"

clone_or_update() {
  local slug="$1"
  local full="$2"
  local dest="$REPOS_DIR/$slug"
  local url
  if [[ -n "$TOKEN" ]]; then
    url="https://x-access-token:${TOKEN}@github.com/${full}.git"
  else
    url="https://github.com/${full}.git"
  fi

  if [[ -d "$dest/.git" ]]; then
    echo "[codegraph] updating $slug"
    git -C "$dest" fetch --depth=1 origin HEAD
    git -C "$dest" reset --hard FETCH_HEAD
  else
    echo "[codegraph] cloning $full -> $dest"
    rm -rf "$dest"
    git clone --depth=1 "$url" "$dest"
  fi

  echo "[codegraph] analyzing $slug"
  (cd "$dest" && gitnexus analyze --skip-agents-md --skip-skills --skip-embeddings || \
     gitnexus analyze --skip-agents-md --skip-skills)
}

if [[ -n "$REPOS_SPEC" ]]; then
  IFS=',' read -ra ENTRIES <<< "$REPOS_SPEC"
  for entry in "${ENTRIES[@]}"; do
    entry="$(echo "$entry" | xargs)"
    [[ -z "$entry" ]] && continue
    if [[ "$entry" == *"|"* ]]; then
      slug="${entry%%|*}"
      full="${entry#*|}"
    else
      full="$entry"
      slug="$(basename "$entry")"
    fi
    clone_or_update "$slug" "$full"
  done
else
  for entry in "${DEFAULT_REPOS[@]}"; do
    slug="${entry%%|*}"
    full="${entry#*|}"
    clone_or_update "$slug" "$full"
  done
fi

echo "[codegraph] indexed repos:"
gitnexus list || true
