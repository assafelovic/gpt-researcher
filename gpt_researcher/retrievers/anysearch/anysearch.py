"""AnySearch API search retriever for GPT Researcher.

AnySearch (https://anysearch.com) is a unified search service exposing general
and vertical search through ``POST /v1/search``. The API key is optional:
requests without a key are served anonymously within the server-side quota.

Environment:
    ANYSEARCH_API_KEY: optional API key. When unset or blank, requests are
        sent anonymously (no ``Authorization`` header at all — never an
        empty Bearer token).

Selection:
    RETRIEVER=anysearch
"""

import json
import logging
import os

import requests

ANYSEARCH_API_URL = "https://api.anysearch.com/v1/search"

#: Client identifier sent as ``X-Anysearch-Client`` so AnySearch can
#: attribute requests to this integration.
ANYSEARCH_CLIENT_ID = "gpt-researcher-anysearch/1.0"

#: Server-side bounds for ``max_results``.
MIN_RESULTS = 1
MAX_RESULTS = 10

_REQUEST_TIMEOUT = 30


class AnySearchRetriever:
    """AnySearch API Retriever.

    Returns web results as ``{href, title, body}`` items whose pages still
    need scraping (``requires_scraping = True``), matching the contract the
    other web retrievers follow.
    """

    # AnySearch returns a title/URL plus a snippet; the real page text is
    # fetched later by the researcher's scraping stage.
    requires_scraping = True

    def __init__(self, query, headers=None, query_domains=None, tag=None,
                 params=None, **kwargs):
        """Initialize the AnySearch retriever.

        Args:
            query: The search query string.
            headers: Optional request headers dict. May also carry
                ``anysearch_api_key``, ``anysearch_tag`` and
                ``anysearch_params`` overrides.
            query_domains: Accepted for interface compatibility; AnySearch
                scoping is expressed through ``tag``/``params`` instead.
            tag: Optional vertical tag, e.g. ``"code.doc"``. See the
                AnySearch domain catalog (``GET /v1/domains``).
            params: Optional dict of vertical parameters for ``tag``.
        """
        self.query = query
        self.headers = headers or {}
        self.query_domains = query_domains or None
        self.api_key = self._resolve_api_key()
        self.tag = tag or self.headers.get("anysearch_tag") or None
        self.params = self._resolve_params(params)
        self.logger = logging.getLogger(__name__)
        # Diagnostics for the last search() call: populated on every call,
        # never holding the API key.
        self.last_request_id = None
        self.last_error = None

    # ------------------------------------------------------------------
    # configuration
    # ------------------------------------------------------------------

    def _resolve_api_key(self):
        """Return the API key, or ``""`` when the request must be anonymous.

        The key is optional: a missing, empty, or whitespace-only key means
        the request goes out with no ``Authorization`` header at all.
        """
        key = (
            self.headers.get("anysearch_api_key")
            or os.environ.get("ANYSEARCH_API_KEY")
            or ""
        )
        return key.strip()

    def _resolve_params(self, params):
        if params:
            return dict(params)
        raw = self.headers.get("anysearch_params")
        if isinstance(raw, dict):
            return dict(raw)
        if isinstance(raw, str) and raw.strip():
            try:
                parsed = json.loads(raw)
                return dict(parsed) if isinstance(parsed, dict) else {}
            except (ValueError, TypeError):
                return {}
        return {}

    def _build_headers(self):
        headers = {
            "Content-Type": "application/json",
            "X-Anysearch-Client": ANYSEARCH_CLIENT_ID,
        }
        # Only authenticate when a real key exists; never send an empty
        # Bearer token, which some servers reject as malformed auth.
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_payload(self, max_results):
        payload = {
            "query": self.query,
            "max_results": max(MIN_RESULTS, min(int(max_results), MAX_RESULTS)),
        }
        if self.tag:
            payload["tag"] = self.tag
        if self.params:
            payload["params"] = self.params
        return payload

    # ------------------------------------------------------------------
    # search
    # ------------------------------------------------------------------

    def search(self, max_results=7):
        """Search AnySearch and return normalized ``{href, title, body}`` items.

        Errors (HTTP failures, non-zero business codes, timeouts, malformed
        responses) are logged with a clear message, recorded on
        ``self.last_error``, and yield ``[]`` — the same convention the other
        retrievers follow. An empty result list therefore always means the
        query genuinely returned nothing, never a swallowed error.
        """
        self.last_request_id = None
        self.last_error = None
        payload = self._build_payload(max_results)

        try:
            response = requests.post(
                ANYSEARCH_API_URL,
                json=payload,
                headers=self._build_headers(),
                timeout=_REQUEST_TIMEOUT,
            )
        except requests.Timeout:
            return self._fail("AnySearch request timed out after "
                              f"{_REQUEST_TIMEOUT}s")
        except requests.RequestException as exc:
            return self._fail(f"AnySearch request failed: {exc}")

        if response.status_code == 401 or response.status_code == 403:
            return self._fail(
                "AnySearch authentication failed "
                f"(HTTP {response.status_code}). The API key is invalid, "
                "revoked, or lacks access; check ANYSEARCH_API_KEY."
            )
        if response.status_code == 429:
            return self._fail(
                "AnySearch rate limit exceeded (HTTP 429). "
                "Anonymous quotas are lower than keyed quotas; retry later "
                "or set ANYSEARCH_API_KEY."
            )
        if not response.ok:
            return self._fail(
                f"AnySearch HTTP error {response.status_code}: "
                f"{response.text[:200]}"
            )

        try:
            data = response.json()
        except ValueError:
            return self._fail("AnySearch returned a non-JSON response.")

        if not isinstance(data, dict):
            return self._fail("AnySearch returned an unexpected response shape.")

        self.last_request_id = data.get("request_id")

        # Business-level status: a non-zero code is an error even on HTTP 200.
        code = data.get("code", 0)
        if code not in (0, "0", None):
            message = data.get("message") or data.get("msg") or "unknown error"
            return self._fail(f"AnySearch API error (code={code}): {message}")

        results = (data.get("data") or {}).get("results") or []
        if not isinstance(results, list):
            return self._fail("AnySearch returned a malformed results payload.")

        normalized = []
        for result in results:
            if not isinstance(result, dict):
                continue
            url = result.get("url") or ""
            if not url:
                continue
            normalized.append({
                "href": url,
                "title": result.get("title") or "",
                "body": result.get("content") or result.get("snippet") or "",
            })
        return normalized

    def _fail(self, message):
        """Record an error and return an empty result list."""
        self.last_error = message
        self.logger.error(message)
        return []
