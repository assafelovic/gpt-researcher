"""
Regression tests: validate_url() and validate_redirect_hook() must reject URLs
whose authority contains a backslash, because urllib.parse (used by the
validator) and urllib3 (used by requests to connect) disagree on the host.

Affected code : gpt_researcher/utils/url_security.py
Affected commit: 9d39a2f86d55e264f69dfeff2365f27fad3c1144

The validator tests FAIL on the affected commit and PASS with the proposed
patch. Network-free: DNS resolution is stubbed and no request is sent.
"""

import socket
from types import SimpleNamespace
from unittest.mock import MagicMock
from urllib.parse import urlparse

import pytest
import requests
from urllib3.util import parse_url

from gpt_researcher.utils import url_security
from gpt_researcher.utils.url_security import UnsafeURLError, validate_redirect_hook, validate_url

# fixture.invalid is reserved by RFC 2606 and never resolves; the stub below
# answers with a globally routable address so only the authority check is
# exercised. The address is never contacted.
STUB_PUBLIC_IP = "8.8.8.8"
AMBIGUOUS_URLS = [
    "http://127.0.0.1\\@fixture.invalid/",
    "https://127.0.0.1:8443\\@fixture.invalid/path",
]


@pytest.fixture
def stub_resolver(monkeypatch):
    resolved = []

    def fake_getaddrinfo(host, *args, **kwargs):
        resolved.append(host)
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (STUB_PUBLIC_IP, 0))]

    monkeypatch.setattr(url_security.socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.delenv("ALLOW_PRIVATE_URLS", raising=False)
    return resolved


def test_urllib_parse_and_urllib3_disagree_on_the_host():
    url = AMBIGUOUS_URLS[0]
    # The host validate_url() resolves and checks:
    assert urlparse(url).hostname == "fixture.invalid"
    # The host urllib3 / requests would connect to:
    assert parse_url(url).host == "127.0.0.1"
    assert parse_url(requests.Request("GET", url).prepare().url).host == "127.0.0.1"


@pytest.mark.parametrize("url", AMBIGUOUS_URLS)
def test_validate_url_rejects_backslash_in_authority(stub_resolver, url):
    with pytest.raises(UnsafeURLError):
        validate_url(url)


def test_redirect_hook_rejects_backslash_in_location(stub_resolver):
    response = SimpleNamespace(
        is_redirect=True,
        url="https://fixture.invalid/start",
        headers={"Location": AMBIGUOUS_URLS[0]},
        close=MagicMock(),
    )

    with pytest.raises(UnsafeURLError):
        validate_redirect_hook(response)
    response.close.assert_called_once()


def test_backslash_outside_the_authority_is_still_allowed(stub_resolver):
    url = "https://fixture.invalid/docs\\file.txt"
    assert validate_url(url) == url
