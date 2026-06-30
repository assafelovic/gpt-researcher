"""Tests for the SSRF / local-file-read URL protections.

These cover the guard used by the scraping and document-loading pipelines to
reject untrusted ``source_urls`` / ``document_urls`` that target internal
services or the local filesystem (see GitHub issues #1794 and #1805).

IP literals are used wherever possible so the checks run without DNS/network.
"""

import socket

import pytest

from gpt_researcher.utils.url_security import (
    UnsafeURLError,
    is_safe_url,
    validate_url,
)


# --- Disallowed schemes / local-file paths (issue #1805) --------------------

@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "file://C:/Windows/win.ini",
        "ftp://example.com/resource",
        "gopher://example.com:70/",
        "/etc/passwd",  # bare local path, no scheme/host
        "C:\\secret\\data.pdf",
        "",
        "   ",
    ],
)
def test_rejects_non_http_and_local_paths(url):
    with pytest.raises(UnsafeURLError):
        validate_url(url)
    assert is_safe_url(url) is False


# --- SSRF: internal / reserved addresses (issue #1794) ----------------------

@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",                                   # loopback
        "http://localhost.localdomain/",                        # resolves to loopback
        "http://169.254.169.254/latest/meta-data/",             # cloud metadata
        "http://10.0.0.5/internal",                             # private /8
        "http://192.168.1.1/admin",                             # private /16
        "http://172.16.0.10/",                                  # private /12
        "http://0.0.0.0/",                                      # unspecified
        "http://[::1]/",                                         # IPv6 loopback
        "http://[fd00::1]/",                                     # IPv6 unique-local
    ],
)
def test_rejects_internal_addresses(url):
    with pytest.raises(UnsafeURLError):
        validate_url(url)


def test_allows_public_ip():
    # 8.8.8.8 is a public address; an IP literal avoids any DNS dependency.
    assert validate_url("http://8.8.8.8/") == "http://8.8.8.8/"
    assert is_safe_url("https://1.1.1.1/path?q=1") is True


# --- DNS rebinding: a public-looking host that resolves internally ----------

def test_blocks_host_resolving_to_private_ip(monkeypatch):
    def fake_getaddrinfo(host, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("10.1.2.3", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(UnsafeURLError):
        validate_url("http://totally-public-looking.example/")


# --- Opt-in escape hatch for trusted / self-hosted deployments --------------

def test_allow_private_argument_bypasses_check():
    assert validate_url("http://127.0.0.1:8000/", allow_private=True) == (
        "http://127.0.0.1:8000/"
    )


def test_allow_private_env_var_bypasses_check(monkeypatch):
    monkeypatch.setenv("ALLOW_PRIVATE_URLS", "true")
    assert is_safe_url("http://192.168.0.10/") is True
    monkeypatch.setenv("ALLOW_PRIVATE_URLS", "false")
    assert is_safe_url("http://192.168.0.10/") is False
