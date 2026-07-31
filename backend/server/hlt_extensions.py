"""HLT-specific extensions for the GPT Researcher FastAPI app.

This module is isolated from upstream code so it can be regenerated or
re-applied after upstream merges without touching `backend/server/app.py`
beyond a single import line.

Adds:
  1. `GET /health` - dedicated liveness probe (Railway healthcheck target).
  2. `X-API-Key` middleware - rejects unauthenticated requests outside the
     frontend shell and static assets. Set `API_AUTH_KEY` in Railway env; if
     unset, the middleware is a no-op (useful for local dev).

Usage (one line at the bottom of `app.py`):

    from server.hlt_extensions import install as install_hlt_extensions
    install_hlt_extensions(app)

Upstream merges: if `app.py` is regenerated, just re-add that one import.
"""
from __future__ import annotations

import base64
import hmac
import importlib.util
import json
import logging
import os
import re
import secrets
import time
from typing import Any, Iterable
import urllib.error
import urllib.request

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from gpt_researcher.utils.langfuse_observability import get_langfuse_runtime_status

logger = logging.getLogger(__name__)
_WS_TOKEN_TTL_SECONDS = 120

# Paths that must remain callable without auth so the frontend + Railway
# healthcheck + static assets keep working. Tight allowlist — every other
# route requires `X-API-Key`.
_PUBLIC_EXACT: set[str] = {"/", "/health", "/favicon.ico"}
_PUBLIC_PREFIXES: tuple[str, ...] = (
    "/site/",      # Next.js static build
    "/static/",    # Any static mounts
)

# The canonical HLT estate repositories for codebase-scoped research. Override
# with a comma-separated HLT_CODEBASE_REPOS env when the estate map changes.
_DEFAULT_CODEBASE_REPOS = (
    "Awhitter/nursing-mastery (nurse-facing frontend — the career home)",
    "Awhitter/ScraperVault (nurse-recruiting backend — jobs, employers, people, applications)",
    "Awhitter/katailyst2 (AI primitives, registry, and creation engine)",
    "Awhitter/MMM2 (multimedia engine)",
    "Awhitter/evidence-based-business (EBB — metrics and analytics layer)",
)

# Katailyst2 is the current generation; www.katailyst.com is v1/legacy.
_DEFAULT_KATAILYST_MCP_URL = "https://katailyst2.vercel.app/mcp"

_SCOPE_INSTRUCTIONS = {
    "codebase": (
        "Use available codebase/repository context. Prefer implementation files, "
        "repo maps, pull requests, and architecture notes over generic web sources."
    ),
    "cms": (
        "Use available Katailyst2 registry, knowledge-base, playbook, skill, and "
        "ecosystem-map context when it is relevant to the question. Do not treat "
        "this as corporate CMS or question-bank access."
    ),
    "qbank": (
        "Use read-only corporate CMS and question-bank context through the "
        "Katailyst hlt-partner-api tool path when it is available. Never write "
        "to corporate CMS/QBank, and clearly say when that source was not inspected."
    ),
    "metrics": (
        "Use available metrics/analytics context, including Metabase-backed data, "
        "when it is relevant. Clearly separate measured data from inference."
    ),
    "firecrawl": (
        "For external pages, prefer high-quality extraction and crawling when the "
        "deployment has Firecrawl configured."
    ),
    "media": (
        "Use Cloudinary media-library context when it is relevant. Treat returned "
        "assets as read-only references for examples, visual direction, and reuse."
    ),
}

_DEPTH_INSTRUCTIONS = {
    "fast": "Keep the research narrow and fast. Prioritize the most relevant sources.",
    "balanced": "Balance speed and depth. Use enough context to answer confidently.",
    "deep": "Go deeper. Compare sources, inspect primary context, and surface tradeoffs.",
}

_SCOPE_KEYS = ("codebase", "cms", "qbank", "metrics", "firecrawl", "media")
_MCP_PRESETS = ("katailyst", "codegraph", "github", "metabase", "apify")
_DEFAULT_APIFY_MCP_URL = "https://mcp.apify.com"
_CLOUDINARY_RESOURCE_TYPES = ("image", "video", "raw")
_CLOUDINARY_MAX_ASSETS = 8
_CLOUDINARY_STOPWORDS = {
    "about",
    "across",
    "after",
    "also",
    "and",
    "are",
    "could",
    "find",
    "for",
    "from",
    "have",
    "help",
    "into",
    "latest",
    "like",
    "make",
    "that",
    "the",
    "this",
    "through",
    "what",
    "when",
    "with",
    "would",
    "your",
}


def api_key_is_valid(provided: str | None) -> bool:
    """Return whether `provided` matches API_AUTH_KEY.

    When API_AUTH_KEY is unset, auth is intentionally disabled for local dev.
    """

    expected = os.getenv("API_AUTH_KEY") or None
    if expected is None:
        return True
    return bool(provided and hmac.compare_digest(provided, expected))


def create_websocket_token() -> str:
    """Create a short-lived token for browser WebSocket clients."""

    api_key = os.getenv("API_AUTH_KEY") or None
    if api_key is None:
        return "local-dev"

    issued_at = str(int(time.time()))
    nonce = secrets.token_urlsafe(18)
    payload = f"{issued_at}.{nonce}"
    signature = hmac.new(api_key.encode(), payload.encode(), "sha256").hexdigest()
    return f"{payload}.{signature}"


def websocket_token_is_valid(token: str | None) -> bool:
    """Validate a short-lived browser WebSocket token."""

    api_key = os.getenv("API_AUTH_KEY") or None
    if api_key is None:
        return True
    if not token:
        return False

    try:
        issued_at_text, nonce, provided_signature = token.split(".", 2)
        issued_at = int(issued_at_text)
    except (TypeError, ValueError):
        return False

    now = int(time.time())
    if issued_at > now + 30 or now - issued_at > _WS_TOKEN_TTL_SECONDS:
        return False

    payload = f"{issued_at_text}.{nonce}"
    expected_signature = hmac.new(api_key.encode(), payload.encode(), "sha256").hexdigest()
    return hmac.compare_digest(provided_signature, expected_signature)


def _bearer_headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _katailyst_mcp_url() -> str:
    """Katailyst MCP endpoint, preferring the Katailyst2 generation."""

    return (
        os.getenv("KATAILYST2_MCP_URL")
        or os.getenv("KATAILYST_MCP_URL")
        or _DEFAULT_KATAILYST_MCP_URL
    )


def _katailyst_mcp_token() -> str | None:
    """Katailyst MCP bearer token, preferring the Katailyst2 (`kata_…`) token."""

    return (
        os.getenv("KATAILYST2_MCP_TOKEN")
        or os.getenv("KATAILYST_MCP_TOKEN")
        or os.getenv("KATAILYST_AUTH_TOKEN")
    )


def _apify_token() -> str | None:
    """Apify token for the hosted Apify MCP server (mcp.apify.com)."""

    return os.getenv("APIFY_TOKEN") or os.getenv("APIFY_API_TOKEN")


def _codebase_repos() -> tuple[str, ...]:
    raw = os.getenv("HLT_CODEBASE_REPOS")
    if raw:
        repos = tuple(part.strip() for part in raw.split(",") if part.strip())
        if repos:
            return repos
    return _DEFAULT_CODEBASE_REPOS


def _scope_instruction(key: str) -> str:
    """Scope instruction text; codebase names the canonical estate repos."""

    if key == "codebase":
        repos = "; ".join(_codebase_repos())
        return (
            "Use available codebase/repository context (prefer codegraph MCP "
            "tools: list_repos, query, context, impact, trace when available). "
            "The canonical HLT "
            f"repositories are: {repos}. Prefer these repositories' implementation "
            "files, repo maps, pull requests, and architecture notes over generic "
            "web sources, ignore legacy/archived repositories unless explicitly "
            "asked, and say which repository each finding came from."
        )
    return _SCOPE_INSTRUCTIONS[key]


def _append_unique_mcp_config(configs: list[dict[str, Any]], config: dict[str, Any]) -> None:
    name = config.get("name")
    if name and any(existing.get("name") == name for existing in configs):
        return
    configs.append(config)


def _firecrawl_import_available() -> bool:
    return importlib.util.find_spec("firecrawl") is not None


def _preset_readiness(preset: str) -> dict[str, Any]:
    if preset == "katailyst":
        token = _katailyst_mcp_token()
        return {
            "status": "ready" if token else "unavailable",
            "configured": bool(token),
            "missing": [] if token else ["KATAILYST2_MCP_TOKEN"],
            "url_configured": bool(
                os.getenv("KATAILYST2_MCP_URL") or os.getenv("KATAILYST_MCP_URL")
            ),
        }
    if preset == "codegraph":
        url = os.getenv("CODEGRAPH_MCP_URL")
        return {
            "status": "ready" if url else "unavailable",
            "configured": bool(url),
            "missing": [] if url else ["CODEGRAPH_MCP_URL"],
            "token_configured": bool(os.getenv("CODEGRAPH_MCP_TOKEN")),
        }
    if preset == "github":
        url = os.getenv("GITHUB_MCP_URL")
        return {
            "status": "ready" if url else "unavailable",
            "configured": bool(url),
            "missing": [] if url else ["GITHUB_MCP_URL"],
            "token_configured": bool(os.getenv("GITHUB_MCP_TOKEN")),
        }
    if preset == "apify":
        token = _apify_token()
        return {
            "status": "ready" if token else "unavailable",
            "configured": bool(token),
            "missing": [] if token else ["APIFY_TOKEN"],
            "url_configured": bool(os.getenv("APIFY_MCP_URL")),
        }
    if preset == "metabase":
        url = os.getenv("METABASE_MCP_URL")
        fallback_token = _katailyst_mcp_token()
        fallback_ready = bool(fallback_token)
        direct_ready = bool(url)
        return {
            "status": "ready" if direct_ready or fallback_ready else "unavailable",
            "configured": direct_ready or fallback_ready,
            "missing": [] if direct_ready or fallback_ready else ["METABASE_MCP_URL", "KATAILYST2_MCP_TOKEN"],
            "token_configured": bool(os.getenv("METABASE_MCP_TOKEN")),
            "provider": "metabase" if direct_ready else "katailyst_metrics_fallback",
        }
    return {
        "status": "unknown",
        "configured": False,
        "missing": [],
    }


def _firecrawl_readiness() -> dict[str, Any]:
    has_key = bool(os.getenv("FIRECRAWL_API_KEY"))
    has_package = _firecrawl_import_available()
    missing = []
    if not has_key:
        missing.append("FIRECRAWL_API_KEY")
    if not has_package:
        missing.append("firecrawl-py")
    return {
        "status": "ready" if has_key and has_package else "unavailable",
        "configured": has_key and has_package,
        "missing": missing,
        "server_url_configured": bool(os.getenv("FIRECRAWL_SERVER_URL")),
        "scraper": "firecrawl" if has_key and has_package else "default",
    }


def _cloudinary_readiness() -> dict[str, Any]:
    missing = [
        key
        for key in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")
        if not os.getenv(key)
    ]
    return {
        "status": "ready" if not missing else "unavailable",
        "configured": not missing,
        "missing": missing,
        "cloud_configured": bool(os.getenv("CLOUDINARY_CLOUD_NAME")),
    }


def _task_terms(task: str) -> list[str]:
    seen: set[str] = set()
    terms: list[str] = []
    for raw in re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{2,}", task.lower()):
        term = raw.strip("_-")
        if len(term) < 3 or term in _CLOUDINARY_STOPWORDS or term in seen:
            continue
        seen.add(term)
        terms.append(term)
        if len(terms) >= 12:
            break
    return terms


def _cloudinary_request(
    *,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    timeout: int = 8,
) -> dict[str, Any]:
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    if not cloud_name or not api_key or not api_secret:
        raise RuntimeError("Cloudinary credentials are not configured.")

    url = f"https://api.cloudinary.com/v1_1/{cloud_name}{path}"
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=payload, method=method)
    basic_token = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
    request.add_header("Authorization", f"Basic {basic_token}")
    if payload is not None:
        request.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed Cloudinary host
        raw = response.read().decode("utf-8")
    parsed = json.loads(raw) if raw else {}
    return parsed if isinstance(parsed, dict) else {}


def _cloudinary_list_assets() -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    resources: list[dict[str, Any]] = []

    try:
        body = _cloudinary_request(
            method="POST",
            path="/resources/search",
            body={
                "expression": "resource_type:image OR resource_type:video OR resource_type:raw",
                "max_results": 60,
                "with_field": ["context", "tags", "metadata"],
            },
        )
        raw_resources = body.get("resources")
        if isinstance(raw_resources, list):
            resources.extend(item for item in raw_resources if isinstance(item, dict))
    except Exception as error:  # pragma: no cover - exercised by integration smoke
        warnings.append(
            "Cloudinary search API unavailable; used resource-list fallback. "
            f"({type(error).__name__})"
        )

    if resources:
        return resources, warnings

    for resource_type in _CLOUDINARY_RESOURCE_TYPES:
        try:
            body = _cloudinary_request(
                method="GET",
                path=f"/resources/{resource_type}/upload?max_results=25",
            )
            raw_resources = body.get("resources")
            if isinstance(raw_resources, list):
                resources.extend(item for item in raw_resources if isinstance(item, dict))
        except urllib.error.HTTPError as error:
            warnings.append(f"Cloudinary {resource_type} assets unavailable: HTTP {error.code}.")
        except Exception as error:  # pragma: no cover - network/runtime dependent
            warnings.append(f"Cloudinary {resource_type} assets unavailable: {type(error).__name__}.")

    return resources, warnings


def _stringify_asset_field(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_stringify_asset_field(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key} {_stringify_asset_field(item)}" for key, item in value.items())
    return str(value)


def _score_cloudinary_asset(asset: dict[str, Any], terms: list[str]) -> int:
    if not terms:
        return 1
    haystack = " ".join(
        _stringify_asset_field(asset.get(key))
        for key in (
            "public_id",
            "asset_folder",
            "folder",
            "filename",
            "tags",
            "context",
            "metadata",
        )
    ).lower()
    return sum(1 for term in terms if term in haystack)


def _summarize_cloudinary_asset(asset: dict[str, Any]) -> dict[str, Any]:
    tags = asset.get("tags")
    safe_tags = [tag for tag in tags if isinstance(tag, str)][:8] if isinstance(tags, list) else []
    return {
        "public_id": asset.get("public_id"),
        "resource_type": asset.get("resource_type"),
        "format": asset.get("format"),
        "asset_folder": asset.get("asset_folder") or asset.get("folder"),
        "width": asset.get("width"),
        "height": asset.get("height"),
        "secure_url": asset.get("secure_url") or asset.get("url"),
        "tags": safe_tags,
    }


def search_cloudinary_assets(task: str) -> dict[str, Any]:
    """Search Cloudinary with server-side credentials and return safe asset metadata."""

    readiness = _cloudinary_readiness()
    if readiness["status"] != "ready":
        return {
            "status": "unavailable",
            "assets": [],
            "warnings": ["Cloudinary media search was requested but credentials are not configured."],
        }

    terms = _task_terms(task)
    try:
        resources, warnings = _cloudinary_list_assets()
    except Exception as error:  # pragma: no cover - defensive boundary
        return {
            "status": "degraded",
            "assets": [],
            "warnings": [f"Cloudinary media search failed: {type(error).__name__}."],
        }

    ranked = [
        (score, index, asset)
        for index, asset in enumerate(resources)
        for score in [_score_cloudinary_asset(asset, terms)]
        if score > 0 or not terms
    ]
    ranked.sort(key=lambda item: (-item[0], item[1]))
    assets = [_summarize_cloudinary_asset(asset) for _, _, asset in ranked[:_CLOUDINARY_MAX_ASSETS]]
    return {
        "status": "ready" if assets else "empty",
        "terms": terms,
        "assets": assets,
        "warnings": warnings,
    }


def _status_from_components(statuses: list[str]) -> str:
    if statuses and all(status == "ready" for status in statuses):
        return "ready"
    if any(status == "ready" for status in statuses):
        return "partial"
    return "unavailable"


_BRAIN_REPO_CARDS: tuple[dict[str, Any], ...] = (
    {
        "slug": "nursing-mastery",
        "github": "Awhitter/nursing-mastery",
        "name": "Nursing Mastery",
        "tagline": "Nurse-facing career home and product surface",
        "capabilities": [
            "Nurse career experience and content surfaces",
            "Apply / recruiting UX that sits on ScraperVault data",
            "Brand-facing product home for Nursing Mastery",
        ],
        "ask_examples": [
            "Where does the nurse apply flow live?",
            "What pages are public vs authenticated?",
        ],
    },
    {
        "slug": "scrapervault",
        "github": "Awhitter/ScraperVault",
        "name": "ScraperVault",
        "tagline": "Nurse-recruiting backend — jobs, employers, people, applications",
        "capabilities": [
            "Jobs, employers, people, and applications data",
            "Recruiting pipelines and semantic layers",
            "Source-of-truth for hiring operations",
        ],
        "ask_examples": [
            "Can we filter employers by specialty?",
            "Where are applications stored?",
        ],
    },
    {
        "slug": "katailyst2",
        "github": "Awhitter/katailyst2",
        "name": "Katailyst2",
        "tagline": "AI primitives, registry, and creation / command hub",
        "capabilities": [
            "Entity registry (skills, prompts, playbooks, KBs)",
            "MCP tool surface for agents",
            "Orchestration and discovery for the estate",
        ],
        "ask_examples": [
            "Is there already a skill for competitor research?",
            "How do agents discover tools?",
        ],
    },
    {
        "slug": "mmm2",
        "github": "Awhitter/MMM2",
        "name": "MMM2",
        "tagline": "Multimedia Maker — images, video, TTS (Cloudinary-primary)",
        "capabilities": [
            "Image / video / TTS generation pipelines",
            "Cloudinary upload and media library integration",
            "Media APIs consumed by other HLT surfaces",
        ],
        "ask_examples": [
            "Can MMM2 generate short recruiter explainers?",
            "Which image models are wired?",
        ],
    },
    {
        "slug": "ebb",
        "github": "Awhitter/evidence-based-business",
        "name": "EBB",
        "tagline": "Metrics and analytics layer",
        "capabilities": [
            "Business metrics and dashboards",
            "Evidence-backed reporting for product decisions",
            "Analytics primitives for Nursing Mastery / recruiting",
        ],
        "ask_examples": [
            "What conversion metrics do we track?",
            "Where do Metabase questions live?",
        ],
    },
)


def get_brain_repos() -> list[dict[str, Any]]:
    """Estate repo cards for the Codebase explorer tab."""
    codegraph = _preset_readiness("codegraph")
    return [
        {
            **card,
            "codegraph_ready": codegraph["status"] == "ready",
        }
        for card in _BRAIN_REPO_CARDS
    ]


def get_brain_vision_documents() -> list[dict[str, Any]]:
    """Load vision markdown for the Vision tab + hybrid research.

    Looks in DOC_PATH/vision first, then repo docs/vision as a tracked fallback.
    """
    candidates = [
        os.path.join(os.getenv("DOC_PATH", "./my-docs"), "vision"),
        os.path.join("docs", "vision"),
        os.path.join(os.path.dirname(__file__), "..", "..", "docs", "vision"),
    ]
    documents: list[dict[str, Any]] = []
    seen: set[str] = set()
    for vision_dir in candidates:
        vision_dir = os.path.abspath(vision_dir)
        if not os.path.isdir(vision_dir):
            continue
        for name in sorted(os.listdir(vision_dir)):
            if not name.endswith(".md") or name in seen:
                continue
            path = os.path.join(vision_dir, name)
            try:
                with open(path, encoding="utf-8") as handle:
                    content = handle.read()
            except OSError as exc:
                logger.warning("Failed to read vision doc %s: %s", path, exc)
                continue
            seen.add(name)
            documents.append(
                {
                    "id": name.removesuffix(".md"),
                    "filename": name,
                    "title": name.removesuffix(".md").replace("-", " ").title(),
                    "content": content,
                    "path": f"vision/{name}",
                }
            )
    return documents


_LINEAR_GRAPHQL_URL = "https://api.linear.app/graphql"
_LINEAR_CACHE_TTL_SECONDS = 300
_linear_cache: dict[str, tuple[float, Any]] = {}


def _linear_graphql(query: str, timeout: int = 8) -> dict[str, Any] | None:
    """Run a Linear GraphQL query with LINEAR_API_KEY. Returns None on any failure."""

    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        return None
    payload = json.dumps({"query": query}).encode("utf-8")
    request = urllib.request.Request(_LINEAR_GRAPHQL_URL, data=payload, method="POST")
    request.add_header("Authorization", api_key)
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed Linear host
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as error:
        logger.warning("Linear GraphQL request failed: %s", type(error).__name__)
        return None
    if not isinstance(body, dict) or body.get("errors"):
        logger.warning("Linear GraphQL returned errors: %s", body.get("errors") if isinstance(body, dict) else "non-dict body")
        return None
    data = body.get("data")
    return data if isinstance(data, dict) else None


def _linear_cached(key: str, fetch) -> Any:
    now = time.time()
    cached = _linear_cache.get(key)
    if cached and now - cached[0] < _LINEAR_CACHE_TTL_SECONDS:
        return cached[1]
    result = fetch()
    if result is not None:
        _linear_cache[key] = (now, result)
    return result


def _fetch_linear_milestones() -> list[dict[str, Any]] | None:
    data = _linear_graphql(
        """
        query {
          projects(first: 25) {
            nodes {
              id
              name
              description
              state
              progress
              targetDate
              url
              updatedAt
            }
          }
        }
        """
    )
    if data is None:
        return None
    nodes = ((data.get("projects") or {}).get("nodes")) or []
    state_rank = {"started": 0, "planned": 1, "backlog": 2, "paused": 3, "completed": 4}
    milestones = []
    for node in nodes:
        state = node.get("state")
        if state == "canceled":
            continue
        milestones.append(
            {
                "id": node.get("id"),
                "title": node.get("name"),
                "summary": node.get("description") or "",
                "status": state,
                "progress": round(float(node.get("progress") or 0.0), 2),
                "target": node.get("targetDate"),
                "url": node.get("url"),
            }
        )
    milestones.sort(key=lambda item: state_rank.get(item["status"], 5))
    return milestones


def _fetch_linear_shipped() -> list[dict[str, Any]] | None:
    since = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 21 * 86400))
    data = _linear_graphql(
        f"""
        query {{
          issues(
            first: 15
            filter: {{ completedAt: {{ gte: "{since}" }} }}
            orderBy: updatedAt
          ) {{
            nodes {{
              id
              identifier
              title
              url
              completedAt
              team {{ name }}
              project {{ name }}
            }}
          }}
        }}
        """
    )
    if data is None:
        return None
    nodes = ((data.get("issues") or {}).get("nodes")) or []
    entries = []
    for node in nodes:
        completed = node.get("completedAt") or ""
        team = (node.get("team") or {}).get("name")
        project = (node.get("project") or {}).get("name")
        context = " · ".join(part for part in [team, project] if part)
        entries.append(
            {
                "id": f"linear-{node.get('identifier')}",
                "date": completed[:10],
                "title": node.get("title"),
                "summary": f"Shipped {node.get('identifier')}" + (f" ({context})" if context else ""),
                "repos": [team] if team else [],
                "kind": "shipped",
                "url": node.get("url"),
                "source": "linear",
            }
        )
    return entries


def get_brain_changelog() -> list[dict[str, Any]]:
    """Changelog feed: recent Linear completions first, then curated seed entries."""
    live: list[dict[str, Any]] = []
    if os.getenv("LINEAR_API_KEY"):
        fetched = _linear_cached("shipped", _fetch_linear_shipped)
        if fetched:
            live = fetched
    return live + [
        {
            "id": "upstream-sync-2026-07",
            "date": "2026-07-30",
            "title": "Synced GPT Researcher to upstream (June 2026)",
            "summary": (
                "Merged upstream retrievers, MiniMax provider, and deep-research "
                "fixes while keeping Mastery Research HLT overlays intact."
            ),
            "repos": ["hlt-gpt-researcher"],
            "kind": "platform",
        },
        {
            "id": "mastery-brain-surfaces",
            "date": "2026-07-30",
            "title": "Mastery Brain tabs: Codebase, Vision, Changelog, Roadmap",
            "summary": (
                "Team-facing brain surfaces landed so marketing and ops can ask "
                "capability questions, store vision, and see what shipped."
            ),
            "repos": ["hlt-gpt-researcher"],
            "kind": "product",
        },
        {
            "id": "codegraph-estate",
            "date": "2026-07-30",
            "title": "Code-graph MCP for the five estate repos",
            "summary": (
                "GitNexus-backed structural search for mmm2, katailyst2, ebb, "
                "scrapervault, and nursing-mastery — preferred for Code scope."
            ),
            "repos": ["mmm2", "katailyst2", "ebb", "scrapervault", "nursing-mastery"],
            "kind": "infrastructure",
        },
    ]


def get_brain_roadmap() -> dict[str, Any]:
    """Roadmap payload: live Linear projects when LINEAR_API_KEY works, else seed."""
    linear_ready = bool(os.getenv("LINEAR_API_KEY") or os.getenv("LINEAR_MCP_URL"))
    if os.getenv("LINEAR_API_KEY"):
        live = _linear_cached("milestones", _fetch_linear_milestones)
        if live:
            return {
                "provider": "linear",
                "linear_configured": True,
                "milestones": live,
                "note": "Live Linear projects (nursingmastery workspace), cached 5 minutes.",
            }
    milestones = [
        {
            "id": "brain-v1",
            "title": "Mastery Brain v1 live for the team",
            "status": "in_progress",
            "summary": "Ask + Codebase + Vision + Changelog + Roadmap tabs; codegraph + Hermes sidecars.",
        },
        {
            "id": "deep-code-qa",
            "title": "Sub-2-minute ‘can we do X?’ answers",
            "status": "planned",
            "summary": "Codegraph + researcher path tuned for nontechnical teammates with visuals.",
        },
        {
            "id": "productboard",
            "title": "Productboard connector",
            "status": "planned",
            "summary": "Wire when API credentials exist; Linear is the primary roadmap source until then.",
        },
    ]
    return {
        "provider": "seed",
        "linear_configured": linear_ready,
        "milestones": milestones,
        "note": (
            "Connect LINEAR_API_KEY or LINEAR_MCP_URL for live Linear milestones. "
            "Productboard stays stubbed until credentials exist."
        ),
    }


def get_hlt_readiness() -> dict[str, Any]:
    """Return browser-safe readiness for HLT scope-backed integrations."""

    preset_statuses = {preset: _preset_readiness(preset) for preset in _MCP_PRESETS}
    firecrawl_status = _firecrawl_readiness()
    cloudinary_status = _cloudinary_readiness()

    integrations = {
        "codebase": {
            # Ready when Katailyst is up and at least one code backend
            # (preferred codegraph, else GitHub) is configured.
            "status": (
                "ready"
                if preset_statuses["katailyst"]["status"] == "ready"
                and (
                    preset_statuses["codegraph"]["status"] == "ready"
                    or preset_statuses["github"]["status"] == "ready"
                )
                else _status_from_components([
                    preset_statuses["katailyst"]["status"],
                    (
                        "ready"
                        if preset_statuses["codegraph"]["status"] == "ready"
                        or preset_statuses["github"]["status"] == "ready"
                        else "unavailable"
                    ),
                ])
            ),
            "components": {
                "katailyst": preset_statuses["katailyst"]["status"],
                "codegraph": preset_statuses["codegraph"]["status"],
                "github": preset_statuses["github"]["status"],
            },
            "missing": sorted(set(
                preset_statuses["katailyst"]["missing"]
                + (
                    []
                    if preset_statuses["codegraph"]["status"] == "ready"
                    or preset_statuses["github"]["status"] == "ready"
                    else preset_statuses["codegraph"]["missing"]
                    + preset_statuses["github"]["missing"]
                )
            )),
        },
        "cms": {
            "status": preset_statuses["katailyst"]["status"],
            "components": {"katailyst": preset_statuses["katailyst"]["status"]},
            "missing": preset_statuses["katailyst"]["missing"],
        },
        "qbank": {
            "status": preset_statuses["katailyst"]["status"],
            "components": {"katailyst": preset_statuses["katailyst"]["status"]},
            "missing": preset_statuses["katailyst"]["missing"],
            "access": "read_only_checked_on_use",
        },
        "metrics": {
            "status": preset_statuses["metabase"]["status"],
            "components": {
                "metabase": "ready" if os.getenv("METABASE_MCP_URL") else "unavailable",
                "katailyst_metrics_fallback": (
                    "ready"
                    if preset_statuses["metabase"].get("provider") == "katailyst_metrics_fallback"
                    else "inactive"
                ),
            },
            "missing": preset_statuses["metabase"]["missing"],
            "provider": preset_statuses["metabase"].get("provider"),
        },
        "firecrawl": {
            "status": firecrawl_status["status"],
            "components": {
                "firecrawl": firecrawl_status["status"],
                "apify": preset_statuses["apify"]["status"],
            },
            "missing": firecrawl_status["missing"],
            "scraper": firecrawl_status["scraper"],
        },
        "media": {
            "status": cloudinary_status["status"],
            "components": {"cloudinary": cloudinary_status["status"]},
            "missing": cloudinary_status["missing"],
            "access": "read_only_server_side",
        },
    }

    status_values = [entry["status"] for entry in integrations.values()]
    ready_count = sum(1 for status in status_values if status == "ready")
    partial_count = sum(1 for status in status_values if status == "partial")
    unavailable_count = sum(1 for status in status_values if status == "unavailable")

    aggregate = "ready"
    if partial_count:
        aggregate = "partial"
    if unavailable_count and ready_count == 0 and partial_count == 0:
        aggregate = "needs_config"
    elif unavailable_count:
        aggregate = "partial"

    return {
        "status": aggregate,
        "integrations": integrations,
        "preset_statuses": preset_statuses,
        "scraper": firecrawl_status,
        "summary": {
            "ready": ready_count,
            "partial": partial_count,
            "unavailable": unavailable_count,
        },
    }


def _mcp_config_for_preset(preset: str, name: str | None = None) -> dict[str, Any] | None:
    name = name or preset
    if preset == "katailyst":
        readiness = _preset_readiness("katailyst")
        if readiness["status"] != "ready":
            logger.warning("Skipping Katailyst MCP preset: KATAILYST2_MCP_TOKEN is unset")
            return None
        url = _katailyst_mcp_url()
        token = _katailyst_mcp_token()
    elif preset == "codegraph":
        readiness = _preset_readiness("codegraph")
        if readiness["status"] != "ready":
            logger.warning("Skipping code-graph MCP preset: CODEGRAPH_MCP_URL is unset")
            return None
        url = os.getenv("CODEGRAPH_MCP_URL")
        token = os.getenv("CODEGRAPH_MCP_TOKEN")
    elif preset == "github":
        readiness = _preset_readiness("github")
        if readiness["status"] != "ready":
            logger.warning("Skipping GitHub MCP preset: GITHUB_MCP_URL is unset")
            return None
        url = os.getenv("GITHUB_MCP_URL")
        token = os.getenv("GITHUB_MCP_TOKEN")
    elif preset == "apify":
        readiness = _preset_readiness("apify")
        if readiness["status"] != "ready":
            logger.warning("Skipping Apify MCP preset: APIFY_TOKEN is unset")
            return None
        url = os.getenv("APIFY_MCP_URL") or _DEFAULT_APIFY_MCP_URL
        token = _apify_token()
    elif preset == "metabase":
        readiness = _preset_readiness("metabase")
        if readiness["status"] != "ready":
            logger.warning("Skipping metrics MCP preset: METABASE_MCP_URL and Katailyst fallback are unavailable")
            return None
        if readiness.get("provider") == "katailyst_metrics_fallback":
            url = _katailyst_mcp_url()
            token = _katailyst_mcp_token()
        else:
            url = os.getenv("METABASE_MCP_URL")
            token = os.getenv("METABASE_MCP_TOKEN")
    else:
        logger.warning("Skipping unknown MCP preset: %s", preset)
        return None

    return {
        "name": name,
        "connection_url": url,
        "connection_type": "streamable_http",
        "connection_headers": _bearer_headers(token),
    }


def expand_mcp_presets(mcp_configs: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Expand HLT server-side MCP presets without exposing tokens to browsers."""

    expanded: list[dict[str, Any]] = []
    for config in mcp_configs or []:
        preset = config.get("preset")
        if not preset:
            expanded.append(config)
            continue

        name = config.get("name") or preset
        expanded_config = _mcp_config_for_preset(preset, name)
        if expanded_config:
            expanded.append(expanded_config)
    return expanded


def _scope_status(
    key: str,
    *,
    requested: bool,
    readiness: dict[str, Any],
) -> dict[str, Any]:
    integration = readiness["integrations"][key]
    status = integration["status"] if requested else "inactive"
    active = requested and status in {"ready", "partial"}
    degraded = requested and status in {"partial", "unavailable"}
    return {
        "requested": requested,
        "status": status,
        "active": active,
        "degraded": degraded,
        "components": integration.get("components", {}),
        "missing": integration.get("missing", []),
        "scraper": integration.get("scraper"),
    }


def resolve_research_scope(
    *,
    mcp_configs: list[dict[str, Any]] | None,
    research_scope: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], str | None, dict[str, Any]]:
    """Resolve browser scope metadata into server-side configs and status."""

    scope = research_scope or {}
    readiness = get_hlt_readiness()
    configs = list(mcp_configs or [])

    requested = {key: bool(scope.get(key)) for key in _SCOPE_KEYS}
    if requested["codebase"] or requested["cms"] or requested["qbank"]:
        _append_unique_mcp_config(configs, {"name": "katailyst", "preset": "katailyst"})
    if requested["codebase"]:
        # Prefer structural code-graph MCP; keep GitHub MCP as fallback.
        codegraph_ready = readiness["preset_statuses"]["codegraph"]["status"] == "ready"
        if codegraph_ready:
            _append_unique_mcp_config(configs, {"name": "codegraph", "preset": "codegraph"})
        else:
            _append_unique_mcp_config(configs, {"name": "github", "preset": "github"})
    if requested["metrics"]:
        _append_unique_mcp_config(configs, {"name": "metabase", "preset": "metabase"})
    if requested["firecrawl"]:
        # Deep-web scope: add Apify's hosted MCP (actor marketplace) when a
        # token exists so research can scrape sources Firecrawl cannot.
        if readiness["preset_statuses"]["apify"]["status"] == "ready":
            _append_unique_mcp_config(configs, {"name": "apify", "preset": "apify"})

    expanded_configs = expand_mcp_presets(configs)
    scope_statuses = {
        key: _scope_status(key, requested=requested[key], readiness=readiness)
        for key in _SCOPE_KEYS
    }
    scraper_override = "firecrawl" if scope_statuses["firecrawl"]["active"] else None

    active_sources = [
        key for key, status in scope_statuses.items()
        if status["active"]
    ]
    degraded_sources = [
        key for key, status in scope_statuses.items()
        if status["degraded"]
    ]

    metadata = {
        "enabled_sources": [key for key in _SCOPE_KEYS if requested[key]],
        "active_sources": active_sources,
        "degraded_sources": degraded_sources,
        "scope_statuses": scope_statuses,
        "preset_statuses": readiness["preset_statuses"],
        "depth": scope.get("depth") if scope.get("depth") in _DEPTH_INSTRUCTIONS else "balanced",
        "mcp_server_count": len(expanded_configs),
        "scraper": {
            "requested": requested["firecrawl"],
            "active": bool(scraper_override),
            "selected": scraper_override or "default",
        },
        "media": {
            "requested": requested["media"],
            "searched": False,
            "asset_count": 0,
        },
    }
    return expanded_configs, scraper_override, metadata


def prepare_research_request(
    *,
    task: str,
    mcp_enabled: bool,
    mcp_strategy: str,
    mcp_configs: list[dict[str, Any]] | None,
    research_scope: dict[str, Any] | None,
) -> tuple[str, bool, str, list[dict[str, Any]], dict[str, Any], str | None]:
    """Apply HLT research-scope metadata to a GPT Researcher request.

    This keeps the browser payload token-free. The frontend sends booleans such
    as `codebase` or `cms`; this server-side helper expands them into safe MCP
    presets and adds concise research instructions to the task.
    """

    scope = research_scope or {}
    enabled_keys = [key for key in _SCOPE_KEYS if bool(scope.get(key))]
    depth = scope.get("depth") if scope.get("depth") in _DEPTH_INSTRUCTIONS else "balanced"

    expanded_configs, scraper_override, hlt_scope_metadata = resolve_research_scope(
        mcp_configs=mcp_configs,
        research_scope=research_scope,
    )
    if bool(scope.get("media")):
        media_result = search_cloudinary_assets(task)
        assets = media_result.get("assets", [])
        hlt_scope_metadata["media"] = {
            "requested": True,
            "searched": media_result.get("status") in {"ready", "empty"},
            "status": media_result.get("status"),
            "asset_count": len(assets) if isinstance(assets, list) else 0,
            "assets": assets if isinstance(assets, list) else [],
            "warnings": media_result.get("warnings", []),
        }
        if media_result.get("status") in {"degraded", "unavailable"}:
            if "media" not in hlt_scope_metadata["degraded_sources"]:
                hlt_scope_metadata["degraded_sources"].append("media")
    next_mcp_enabled = bool(mcp_enabled or expanded_configs)
    next_mcp_strategy = "fast" if depth == "fast" else "deep"

    if not enabled_keys and depth == "balanced":
        return task, next_mcp_enabled, mcp_strategy, expanded_configs, hlt_scope_metadata, scraper_override

    instruction_lines = [_DEPTH_INSTRUCTIONS[depth]]
    instruction_lines.extend(
        _scope_instruction(key)
        for key in hlt_scope_metadata["active_sources"]
        if key in _SCOPE_INSTRUCTIONS
    )
    for key in hlt_scope_metadata["degraded_sources"]:
        if key in enabled_keys:
            instruction_lines.append(
                f"{key} scope was requested but is only partially available or unconfigured; "
                "do not imply unavailable internal data was inspected."
            )
    media = hlt_scope_metadata.get("media", {})
    media_assets = media.get("assets") if isinstance(media, dict) else []
    if isinstance(media_assets, list) and media_assets:
        instruction_lines.append(
            "Cloudinary media assets found below are read-only references. Cite public_id or URL when useful."
        )
    scoped_task = (
        f"{task}\n\n"
        "HLT research scope instructions:\n"
        + "\n".join(f"- {line}" for line in instruction_lines)
    )
    if isinstance(media_assets, list) and media_assets:
        scoped_task += "\n\nCloudinary media library context:\n" + "\n".join(
            "- "
            + "; ".join(
                part
                for part in [
                    f"public_id={asset.get('public_id')}",
                    f"type={asset.get('resource_type')}",
                    f"folder={asset.get('asset_folder')}" if asset.get("asset_folder") else "",
                    f"tags={', '.join(asset.get('tags') or [])}" if asset.get("tags") else "",
                    f"url={asset.get('secure_url')}" if asset.get("secure_url") else "",
                ]
                if part
            )
            for asset in media_assets
            if isinstance(asset, dict)
        )

    return scoped_task, next_mcp_enabled, next_mcp_strategy, expanded_configs, hlt_scope_metadata, scraper_override


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Reject requests missing a valid `X-API-Key` header.

    No-op when `API_AUTH_KEY` env is unset (local dev / upstream default).
    """

    def __init__(self, app, api_key: str | None, public_exact: set[str], public_prefixes: tuple[str, ...]):
        super().__init__(app)
        self._api_key = api_key
        self._public_exact = public_exact
        self._public_prefixes = public_prefixes

    async def dispatch(self, request: Request, call_next):
        if self._api_key is None:
            return await call_next(request)

        path = request.url.path
        if path in self._public_exact or path.startswith(self._public_prefixes):
            return await call_next(request)

        # CORS preflight must pass; CORSMiddleware handles the actual check.
        if request.method == "OPTIONS":
            return await call_next(request)

        provided = request.headers.get("x-api-key", "")
        if not provided:
            auth_header = request.headers.get("authorization", "")
            if auth_header.lower().startswith("bearer "):
                provided = auth_header[7:].strip()
        if not provided or not hmac.compare_digest(provided, self._api_key):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid X-API-Key header"},
            )
        return await call_next(request)


def install(
    app: FastAPI,
    *,
    extra_public_exact: Iterable[str] | None = None,
    extra_public_prefixes: Iterable[str] | None = None,
) -> None:
    """Attach HLT extensions to the given FastAPI app."""

    public_exact = set(_PUBLIC_EXACT)
    if extra_public_exact:
        public_exact.update(extra_public_exact)

    public_prefixes = list(_PUBLIC_PREFIXES)
    if extra_public_prefixes:
        public_prefixes.extend(extra_public_prefixes)

    # 1. /health — used by Railway healthcheckPath (see railway.toml).
    @app.get("/health", tags=["hlt"])
    def health():  # noqa: D401
        readiness = get_hlt_readiness()
        return {
            "status": "ok",
            "service": "gpt-researcher-api",
            "version": os.getenv("RAILWAY_GIT_COMMIT_SHA", "local")[:7],
            "deploy_marker": os.getenv("HLT_DEPLOY_MARKER", "local"),
            "observability": {
                "langfuse": get_langfuse_runtime_status(),
            },
            "integrations": {
                "status": readiness["status"],
                "summary": readiness["summary"],
            },
        }

    @app.get("/api/hlt/readiness", tags=["hlt"])
    def readiness():  # noqa: D401
        return get_hlt_readiness()

    @app.post("/gather", tags=["hlt"])
    async def katailyst_gather(request: Request):  # noqa: D401
        """Katailyst2 HTTP gather adapter — maps quick_search results to typed findings."""
        from gpt_researcher import GPTResearcher

        body = await request.json()
        query_obj = body.get("query") or {}
        keyword = (
            query_obj.get("keyword")
            or query_obj.get("query")
            or query_obj.get("url")
            or ""
        )
        if not keyword:
            return JSONResponse(status_code=400, content={"detail": "query.keyword required"})

        max_findings = min(int(body.get("max_findings") or 10), 25)
        research_kind = body.get("research_kind") or "topic_deep_dive"

        kind_to_finding = {
            "seo_research": "content_gap",
            "competitor_research": "content_gap",
            "trend_scan": "trend",
            "forum_scan": "pain",
            "audience_language_mining": "language",
            "topic_deep_dive": "topic_opportunity",
            "cross_industry_scan": "trend",
        }
        default_finding = kind_to_finding.get(research_kind, "topic_opportunity")

        researcher = GPTResearcher(query=str(keyword), report_type="research_report")
        results = await researcher.quick_search(
            query=str(keyword),
            query_domains=query_obj.get("domains"),
            aggregated_summary=True,
        )

        findings = []
        if isinstance(results, str) and results.strip():
            findings.append(
                {
                    "finding_type": default_finding,
                    "summary": results.strip()[:240],
                    "detail_md": results.strip()[:4000],
                    "source_kind": "gpt_researcher",
                    "confidence": 0.72,
                }
            )
        elif isinstance(results, list):
            for item in results[:max_findings]:
                if isinstance(item, dict):
                    summary = str(item.get("title") or item.get("content") or item.get("snippet") or keyword)[:240]
                    url = item.get("url") or item.get("link")
                    findings.append(
                        {
                            "finding_type": default_finding,
                            "summary": summary,
                            "detail_md": str(item.get("content") or item.get("snippet") or summary)[:4000],
                            "source_url": url,
                            "source_kind": "gpt_researcher",
                            "confidence": 0.7,
                        }
                    )
                elif isinstance(item, str) and item.strip():
                    findings.append(
                        {
                            "finding_type": default_finding,
                            "summary": item.strip()[:240],
                            "detail_md": item.strip()[:4000],
                            "source_kind": "gpt_researcher",
                            "confidence": 0.65,
                        }
                    )

        return {"findings": findings[:max_findings], "cost_usd": 0.01, "external_scan_id": None}

    @app.get("/api/brain/repos", tags=["hlt", "brain"])
    def brain_repos():  # noqa: D401
        """Team-facing estate repo concept cards for the Codebase tab."""
        return {"repos": get_brain_repos()}

    @app.get("/api/brain/vision", tags=["hlt", "brain"])
    def brain_vision():  # noqa: D401
        """Markdown vision docs from DOC_PATH/vision (hybrid research corpus)."""
        return {"documents": get_brain_vision_documents()}

    @app.get("/api/brain/changelog", tags=["hlt", "brain"])
    def brain_changelog():  # noqa: D401
        """Interactive changelog feed (static seed + optional Linear later)."""
        return {"entries": get_brain_changelog()}

    @app.get("/api/brain/roadmap", tags=["hlt", "brain"])
    def brain_roadmap():  # noqa: D401
        """Roadmap milestones (Linear when configured; otherwise seed)."""
        return get_brain_roadmap()

    # 2. API-key auth (opt-in via env).
    api_key = os.getenv("API_AUTH_KEY") or None
    app.add_middleware(
        APIKeyMiddleware,
        api_key=api_key,
        public_exact=public_exact,
        public_prefixes=tuple(public_prefixes),
    )

    if api_key:
        logger.info("HLT extensions: /health + X-API-Key middleware installed (auth enabled)")
    else:
        logger.info("HLT extensions: /health installed; auth disabled (API_AUTH_KEY unset)")
