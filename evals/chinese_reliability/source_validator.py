"""Lightweight URL normalization and availability checks for evaluations."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


SourceStatus = Literal["valid", "invalid", "blocked"]
Fetcher = Callable[[str, float], Awaitable["FetchResponse"]]

TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "spm",
}
BLOCKED_STATUS_CODES = {401, 403, 429}


@dataclass(frozen=True)
class FetchResponse:
    final_url: str
    status_code: int
    content: bytes


@dataclass(frozen=True)
class SourceValidationResult:
    original_url: str
    normalized_url: str
    final_url: str | None
    status: SourceStatus
    http_status: int | None
    content_length: int
    reason: str


def _is_tracking_key(key: str) -> bool:
    lowered = key.lower()
    return lowered.startswith("utm_") or lowered in TRACKING_QUERY_KEYS


def normalize_url(url: str) -> str:
    """Return a stable HTTP(S) URL without tracking parameters or fragments."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string")

    parsed = urlsplit(url.strip())
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only absolute HTTP(S) URLs are supported")

    host = parsed.hostname.lower()
    port = parsed.port
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"
    else:
        netloc = host

    path = parsed.path or ""
    if path != "/":
        path = path.rstrip("/")

    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not _is_tracking_key(key)
    ]
    query = urlencode(sorted(query_items))
    return urlunsplit((scheme, netloc, path, query, ""))


def deduplicate_urls(urls: Iterable[str]) -> list[str]:
    """Normalize URLs and retain their first-seen order."""
    unique_urls: list[str] = []
    seen: set[str] = set()
    for url in urls:
        try:
            normalized = normalize_url(url)
        except (TypeError, ValueError):
            continue
        if normalized not in seen:
            seen.add(normalized)
            unique_urls.append(normalized)
    return unique_urls


class SourceValidator:
    """Validate URL reachability with bounded concurrency and downloads."""

    def __init__(
        self,
        *,
        fetcher: Fetcher | None = None,
        timeout_seconds: float = 8.0,
        concurrency: int = 5,
        min_content_bytes: int = 200,
        max_download_bytes: int = 4096,
    ) -> None:
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        self.timeout_seconds = timeout_seconds
        self.min_content_bytes = min_content_bytes
        self.max_download_bytes = max_download_bytes
        self._semaphore = asyncio.Semaphore(concurrency)
        self._fetcher = fetcher or self._fetch

    async def validate_many(self, urls: Iterable[str]) -> list[SourceValidationResult]:
        entries: list[tuple[str, str | None]] = []
        seen: set[tuple[str, str]] = set()
        for value in urls:
            original_url = value if isinstance(value, str) else str(value)
            try:
                normalized_url = normalize_url(original_url)
                key = ("valid", normalized_url)
            except (TypeError, ValueError):
                normalized_url = None
                key = ("invalid", original_url)
            if key not in seen:
                seen.add(key)
                entries.append((original_url, normalized_url))

        return await asyncio.gather(
            *(self._validate_entry(original, normalized) for original, normalized in entries)
        )

    async def _validate_entry(
        self, original_url: str, normalized_url: str | None
    ) -> SourceValidationResult:
        if normalized_url is None:
            return SourceValidationResult(
                original_url=original_url,
                normalized_url="",
                final_url=None,
                status="invalid",
                http_status=None,
                content_length=0,
                reason="invalid_url",
            )
        return await self._validate_one(original_url, normalized_url)

    async def _validate_one(
        self, original_url: str, normalized_url: str
    ) -> SourceValidationResult:
        async with self._semaphore:
            try:
                response = await self._fetcher(normalized_url, self.timeout_seconds)
            except (TimeoutError, socket.timeout, asyncio.TimeoutError):
                return self._failure(original_url, normalized_url, "timeout")
            except URLError as exc:
                reason = "timeout" if isinstance(exc.reason, socket.timeout) else "network_error"
                return self._failure(original_url, normalized_url, reason)
            except Exception as exc:
                return self._failure(original_url, normalized_url, type(exc).__name__)

        content_length = len(response.content)
        final_url = self._safe_normalize(response.final_url)
        if response.status_code in BLOCKED_STATUS_CODES:
            status: SourceStatus = "blocked"
            reason = f"http_{response.status_code}"
        elif not 200 <= response.status_code < 300:
            status = "invalid"
            reason = f"http_{response.status_code}"
        elif content_length < self.min_content_bytes:
            status = "invalid"
            reason = "content_too_short"
        else:
            status = "valid"
            reason = "ok"

        return SourceValidationResult(
            original_url=original_url,
            normalized_url=normalized_url,
            final_url=final_url,
            status=status,
            http_status=response.status_code,
            content_length=content_length,
            reason=reason,
        )

    async def _fetch(self, url: str, timeout_seconds: float) -> FetchResponse:
        return await asyncio.to_thread(self._fetch_sync, url, timeout_seconds)

    def _fetch_sync(self, url: str, timeout_seconds: float) -> FetchResponse:
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 GPT-Researcher-Reliability-Eval/1.0",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                return FetchResponse(
                    final_url=response.geturl(),
                    status_code=response.status,
                    content=response.read(self.max_download_bytes),
                )
        except HTTPError as exc:
            return FetchResponse(
                final_url=exc.geturl(),
                status_code=exc.code,
                content=exc.read(self.max_download_bytes),
            )

    @staticmethod
    def _safe_normalize(url: str) -> str | None:
        try:
            return normalize_url(url)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _failure(
        original_url: str, normalized_url: str, reason: str
    ) -> SourceValidationResult:
        return SourceValidationResult(
            original_url=original_url,
            normalized_url=normalized_url,
            final_url=None,
            status="invalid",
            http_status=None,
            content_length=0,
            reason=reason,
        )
