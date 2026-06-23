"""URL security utilities for GPT Researcher.

These helpers protect the scraping and document-loading pipelines against
Server-Side Request Forgery (SSRF) and arbitrary local-file reads when the URLs
originate from untrusted input (e.g. the ``source_urls`` / ``document_urls``
parameters accepted by the API and WebSocket endpoints).

By default only ``http`` / ``https`` URLs whose host resolves to a public IP
address are allowed. This blocks:

* Non-HTTP schemes such as ``file://``, ``ftp://`` and ``gopher://``.
* Local filesystem paths (no scheme/host), which some document loaders would
  otherwise read directly from disk (arbitrary local file read).
* Requests to private, loopback, link-local, reserved or otherwise internal
  addresses (e.g. ``127.0.0.1``, ``10.0.0.0/8`` and the ``169.254.169.254``
  cloud metadata endpoint).

Operators who intentionally scrape internal or self-hosted resources can opt out
of the private-address check by setting the environment variable
``ALLOW_PRIVATE_URLS=true`` (or by passing ``allow_private=True``).

Note: resolving the host here and letting the HTTP client re-resolve it later
leaves a small TOCTOU/DNS-rebinding window. Closing it fully requires pinning the
validated IP into the connection; this guard is intended as defence-in-depth that
removes the trivial, unauthenticated SSRF and local-file-read primitives.
"""

from __future__ import annotations

import ipaddress
import os
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = ("http", "https")

_TRUTHY = ("1", "true", "yes", "on")


class UnsafeURLError(ValueError):
    """Raised when a URL is rejected by the SSRF / local-file protections."""


def _private_urls_allowed() -> bool:
    return os.getenv("ALLOW_PRIVATE_URLS", "").strip().lower() in _TRUTHY


def _is_disallowed_ip(ip) -> bool:
    """Return True if the address is not safe to contact (i.e. internal)."""
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def validate_url(url: str, *, allow_private: bool | None = None) -> str:
    """Validate that ``url`` is safe to fetch and return it unchanged.

    Args:
        url: The URL to validate.
        allow_private: When ``True``, skip the private/internal address check.
            When ``None`` (default), fall back to the ``ALLOW_PRIVATE_URLS``
            environment variable.

    Returns:
        The original ``url`` if it passes all checks.

    Raises:
        UnsafeURLError: If the URL uses a disallowed scheme, lacks a host, or
            resolves to a non-public address.
    """
    if not isinstance(url, str) or not url.strip():
        raise UnsafeURLError("URL must be a non-empty string.")

    parsed = urlparse(url.strip())

    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise UnsafeURLError(
            f"URL scheme {scheme or '(none)'!r} is not allowed; "
            "only http and https URLs may be fetched."
        )

    host = parsed.hostname
    if not host:
        raise UnsafeURLError("URL must include a valid host.")

    if allow_private is None:
        allow_private = _private_urls_allowed()
    if allow_private:
        return url

    try:
        addrinfo = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"Could not resolve host {host!r}: {exc}") from exc

    for info in addrinfo:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError as exc:
            raise UnsafeURLError(
                f"Host {host!r} resolved to an invalid address {ip_str!r}."
            ) from exc
        if _is_disallowed_ip(ip):
            raise UnsafeURLError(
                f"URL host {host!r} resolves to a non-public address ({ip_str}); "
                "set ALLOW_PRIVATE_URLS=true to allow internal targets."
            )

    return url


def is_safe_url(url: str, *, allow_private: bool | None = None) -> bool:
    """Return ``True`` if ``url`` passes :func:`validate_url`, else ``False``."""
    try:
        validate_url(url, allow_private=allow_private)
        return True
    except UnsafeURLError:
        return False
